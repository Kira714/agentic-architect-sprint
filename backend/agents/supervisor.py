"""
The Supervisor Agent
Orchestrates the workflow and decides routing.
"""
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote, SafetyStatus, ClinicalStatus


def create_supervisor_agent(llm: ChatOpenAI):
    """
    Factory function to create the Supervisor agent.
    
    Creates and returns a node function that orchestrates the workflow by making routing
    decisions. The Supervisor is the central decision-maker in the Supervisor-Worker pattern.
    It analyzes the complete workflow state and routes to appropriate agents based on
    workflow needs, or decides to halt for human review.
    
    Args:
        llm: The ChatOpenAI instance to use for LLM calls
        
    Returns:
        A node function (supervisor_node) that can be used in the LangGraph workflow
    """
    
    async def supervisor_node(state: FoundryState) -> FoundryState:
        """
        Supervisor node function - orchestrates workflow and makes routing decisions.
        
        This function is called by LangGraph as the entry point and after each worker
        agent completes. It analyzes the complete workflow state and decides the next step:
        
        Routing Logic (in order):
        1. If approved → route to "approve"
        2. If halted → route to "halt"
        3. If max iterations reached → route to "halt"
        4. If loop detected (same decision 3x after 5 iterations) → route to "halt"
        5. If no draft → route to "draftsman"
        6. If draft exists, no safety review → route to "safety_guardian"
        7. If safety = critical/flagged → route to "draftsman" (fix safety)
        8. If safety = passed, no clinical review → route to "clinical_critic"
        9. If clinical = needs_revision/rejected → route to "draftsman" (fix quality)
        10. If both passed, debate incomplete → route to "debate_moderator"
        11. If all complete → route to "halt"
        
        The Supervisor uses LLM reasoning to make decisions, but has fallback logic
        if the LLM returns an invalid decision. It also tracks iterations and detects
        infinite loops to prevent the workflow from getting stuck.
        
        Args:
            state: The current FoundryState containing all workflow information
            
        Returns:
            Updated FoundryState with:
            - next_action: The routing decision (draftsman, safety_guardian, clinical_critic,
                          debate_moderator, halt, or approve)
            - agent_notes: Thinking notes and decision notes added by this agent
            - current_agent: Set to SUPERVISOR
            - last_updated: Timestamp of this update
            
        Note:
            The state is automatically checkpointed by LangGraph after this function completes.
            The next_action field is used by the route_decision function in graph.py to
            determine which node to execute next.
        """
        print(f"[SUPERVISOR] Making routing decision (Iteration {state.get('iteration_count', 0)})")
        
        # Check if human has approved
        if state.get('is_approved'):
            decision = "approve"
        # Check if halted for human review
        elif state.get('is_halted') or state.get('awaiting_human_approval'):
            decision = "halt"
        # Check max iterations
        elif state.get('iteration_count', 0) >= state.get('max_iterations', 10):
            print("[SUPERVISOR] Max iterations reached, halting for human review")
            decision = "halt"
        # Self-correction: Detect infinite loops
        elif state.get('iteration_count', 0) >= 5:
            # Check if we're stuck in a loop (same decision repeated)
            recent_decisions = [
                note.get('context', {}).get('decision') 
                for note in state.get('agent_notes', [])[-10:]
                if note.get('agent') == AgentRole.SUPERVISOR and 'decision' in note.get('context', {})
            ]
            if len(recent_decisions) >= 3 and len(set(recent_decisions[-3:])) == 1:
                print(f"[SUPERVISOR] Detected potential loop (same decision {recent_decisions[-1]} repeated). Halting for human review.")
                decision = "halt"
        else:
            # Need to make routing decision - will be set below
            decision = None
        
        # Build context for supervisor decision (only if decision not set yet)
        if decision is None:
            has_draft = bool(state.get('current_draft'))
            has_safety_review = bool(state.get('safety_review'))
            has_clinical_review = bool(state.get('clinical_review'))
            
            safety_status = state.get('safety_review', {}).get('status') if has_safety_review else None
            clinical_status = state.get('clinical_review', {}).get('status') if has_clinical_review else None
            
            # System prompt for Supervisor - AGGRESSIVE, PRECISE, TO THE POINT
            system_prompt = """MISSION: Produce a safe, empathetic, and structured CBT exercise based on user intent.

YOU: Supervisor routing decisions. ONE JOB: Route correctly. NO ERRORS.

ROUTING RULES (EXACT ORDER):
1. No draft → draftsman
2. Draft exists, no safety review → safety_guardian
3. Safety = critical/flagged → draftsman (fix safety)
4. Safety = passed, no clinical review → clinical_critic
5. Clinical = needs_revision/rejected → draftsman (fix quality)
6. Both passed, debate incomplete → debate_moderator
7. All complete → halt
8. Max iterations → halt

RESPONSE: ONE WORD ONLY: draftsman, safety_guardian, clinical_critic, debate_moderator, halt

NO EXPLANATIONS. NO DEVIATIONS. ROUTE CORRECTLY."""
            
            # Build decision context
            debate_complete = state.get('debate_complete', False)
            
            context = f"""Current State:
- Has draft: {has_draft}
- Safety review status: {safety_status.value if safety_status else 'None'}
- Clinical review status: {clinical_status.value if clinical_status else 'None'}
- Debate complete: {debate_complete}
- Iteration: {state.get('iteration_count', 0)}/{state.get('max_iterations', 10)}
- User intent: {state.get('user_intent', 'N/A')}"""
            
            if safety_status:
                context += f"\nSafety concerns: {len(state.get('safety_review', {}).get('concerns', []))}"
            
            if clinical_status:
                scores = state.get('clinical_review', {})
                context += f"\nClinical scores - Empathy: {scores.get('empathy_score', 0):.1f}, Tone: {scores.get('tone_score', 0):.1f}, Structure: {scores.get('structure_score', 0):.1f}"
            
            prompt = f"""{context}

What should be the next step?"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            # Get thinking/reasoning from LLM
            thinking_prompt = f"""{system_prompt}

{context}

Think step by step about what should happen next. Explain your reasoning, then give your decision."""
            
            thinking_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=thinking_prompt)
            ]
            
            # Use a model that supports reasoning (or chain-of-thought)
            response = await llm.ainvoke(thinking_messages)
            response_content = response.content.strip()
            
            # Extract thinking and decision
            thinking = ""
            decision = ""
            
            # Try to extract thinking (everything before the decision)
            if "decision:" in response_content.lower():
                parts = response_content.lower().split("decision:")
                thinking = parts[0].strip()
                decision = parts[1].strip().split()[0] if parts[1] else ""
            elif "\n" in response_content:
                # If multiline, last line might be decision
                lines = response_content.split("\n")
                decision = lines[-1].strip().lower()
                thinking = "\n".join(lines[:-1]).strip()
            else:
                # Single word response
                decision = response_content.lower()
                thinking = f"Based on the current state, I need to route to the next appropriate agent."
            
            # Store thinking in agent notes (use "Thinking:" prefix for streaming)
            thinking_note: AgentNote = {
                "agent": AgentRole.SUPERVISOR,
                "timestamp": datetime.now().isoformat(),
                "message": f"Thinking: {thinking}",
                "context": {"thinking": thinking, "decision": decision}
            }
            
            # Validate and normalize decision
            valid_decisions = ["draftsman", "safety_guardian", "clinical_critic", "debate_moderator", "halt", "approve"]
            if decision not in valid_decisions:
                # Fallback logic - strict workflow sequence
                if not has_draft:
                    decision = "draftsman"
                elif not has_safety_review:
                    decision = "safety_guardian"
                elif safety_status in [SafetyStatus.CRITICAL, SafetyStatus.FLAGGED]:
                    decision = "draftsman"
                elif not has_clinical_review:
                    decision = "clinical_critic"
                elif clinical_status == ClinicalStatus.NEEDS_REVISION:
                    decision = "draftsman"
                elif not debate_complete and safety_status == SafetyStatus.PASSED and clinical_status == ClinicalStatus.APPROVED:
                    decision = "debate_moderator"
                else:
                    decision = "halt"
        
        # Add detailed supervisor notes - all as thinking messages
        decision_messages = {
            "draftsman": "Routing to Draftsman to create/revise the CBT exercise draft using evidence-based protocols.",
            "safety_guardian": "Routing to Safety Guardian to conduct comprehensive safety review with zero tolerance for risks.",
            "clinical_critic": "Routing to Clinical Critic to evaluate clinical quality using rigorous evidence-based criteria.",
            "debate_moderator": "Routing to Debate Moderator to facilitate systematic internal debate ensuring clinical excellence.",
            "halt": "Workflow complete. Halting for human review and approval.",
            "approve": "All reviews passed. Approving final protocol."
        }
        
        # Add decision note as thinking
        decision_note: AgentNote = {
            "agent": AgentRole.SUPERVISOR,
            "timestamp": datetime.now().isoformat(),
            "message": f"Thinking: {decision_messages.get(decision, f'Routing decision: {decision}')} (Iteration {state.get('iteration_count', 0)})",
            "context": {"decision": decision, "iteration": state.get('iteration_count', 0)}
        }
        
        # Combine thinking note and decision note (both are thinking)
        notes_to_add = []
        if 'thinking_note' in locals():
            notes_to_add.append(thinking_note)
        notes_to_add.append(decision_note)
        
        print(f"[SUPERVISOR] Decision: {decision}")
        
        # Store decision in state for routing
        return {
            **state,
            "next_action": decision,  # Store routing decision
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.SUPERVISOR,
            "last_updated": datetime.now().isoformat()
        }
    
    return supervisor_node

