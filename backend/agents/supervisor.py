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
    """Create the Supervisor agent"""
    
    async def supervisor_node(state: FoundryState) -> FoundryState:
        """
        Supervisor decides the next step in the workflow.
        Routes to appropriate agents or decides to halt for human review.
        """
        print(f"[SUPERVISOR] Making routing decision (Iteration {state.get('iteration_count', 0)})")
        
        # Check if human has approved
        if state.get('is_approved'):
            decision = "approve"
        # Check if halted for human review (including awaiting user response to questions)
        elif state.get('is_halted') or state.get('awaiting_human_approval') or state.get('awaiting_user_response'):
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
            
            # System prompt for Supervisor
            system_prompt = """You are the Supervisor orchestrating a rigorous, evidence-based Cognitive Behavioral Therapy (CBT) exercise design workflow. Your role is CRITICAL and requires PRECISION, CONTEXT-AWARENESS, and STRICT ADHERENCE to clinical protocols.

MANDATORY REQUIREMENTS:
1. ALL decisions MUST be evidence-based and grounded in peer-reviewed CBT research
2. ALL routing decisions MUST be contextually aware of the current state and workflow progression
3. ALL decisions MUST prioritize clinical rigor, safety, and therapeutic effectiveness
4. NO deviations from established clinical protocols are permitted
5. ALL state transitions MUST be logically sound and clinically justified

YOUR TEAM (STRICT PROTOCOLS):
1. Information Gatherer - Determines if user-specific information is required for personalization (ONLY when necessary)
2. Draftsman - Creates/revises CBT exercises using EVIDENCE-BASED protocols with CLINICAL RIGOR
3. Safety Guardian - Conducts COMPREHENSIVE safety review with ZERO TOLERANCE for safety risks
4. Clinical Critic - Evaluates clinical quality using RIGOROUS evidence-based criteria
5. Debate Moderator - Facilitates SYSTEMATIC internal debate to ensure CLINICAL EXCELLENCE

MANDATORY WORKFLOW PROTOCOL (STRICT SEQUENCE):
1. If information_gathered = FALSE → route to Information Gatherer (MANDATORY)
2. If information_gathered = TRUE AND current_draft = NULL → route to Draftsman (MANDATORY)
3. If current_draft EXISTS AND safety_review = NULL → route to Safety Guardian (MANDATORY)
4. If safety_review.status = "critical" OR "flagged" → route to Draftsman for revision (MANDATORY)
5. If safety_review.status = "passed" AND clinical_review = NULL → route to Clinical Critic (MANDATORY)
6. If clinical_review.status = "needs_revision" OR "rejected" → route to Draftsman (MANDATORY)
7. If safety_review.status = "passed" AND clinical_review.status = "approved" AND debate_complete = FALSE → route to Debate Moderator (MANDATORY)
8. If debate_complete = TRUE AND both reviews passed → route to halt for human approval (MANDATORY)
9. If iteration_count >= max_iterations → route to halt (MANDATORY - prevents infinite loops)
10. If awaiting_user_response = TRUE → route to halt (MANDATORY - user input required)

CONTEXT-AWARENESS REQUIREMENTS:
- Analyze the COMPLETE state before making ANY routing decision
- Consider ALL agent notes, reviews, and state variables
- Ensure NO redundant routing (detect and prevent loops)
- Maintain STRICT adherence to workflow sequence

RESPONSE FORMAT:
Respond with EXACTLY ONE word from: information_gatherer, draftsman, safety_guardian, clinical_critic, debate_moderator, halt

NO EXPLANATIONS. NO DEVIATIONS. STRICT COMPLIANCE REQUIRED."""
            
            # Build decision context
            information_gathered = state.get('information_gathered', False)
            debate_complete = state.get('debate_complete', False)
            
            context = f"""Current State:
- Information gathered: {information_gathered}
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
            valid_decisions = ["information_gatherer", "draftsman", "safety_guardian", "clinical_critic", "debate_moderator", "halt", "approve"]
            if decision not in valid_decisions:
                # Fallback logic
                # Don't route to information_gatherer if we're already awaiting user response
                if not information_gathered and not state.get('awaiting_user_response'):
                    decision = "information_gatherer"
                elif not has_draft:
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
            "information_gatherer": "Routing to Information Gatherer to ask user for specific details needed for personalization.",
            "draftsman": "Routing to Draftsman to create/revise the CBT exercise draft.",
            "safety_guardian": "Routing to Safety Guardian to review the draft for safety concerns.",
            "clinical_critic": "Routing to Clinical Critic to evaluate clinical quality and empathy.",
            "debate_moderator": "Routing to Debate Moderator to facilitate internal debate and refinement.",
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

