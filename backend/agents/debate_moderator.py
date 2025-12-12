"""
The Debate Moderator Agent
Facilitates internal debate between agents to refine the draft before finalizing.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote


def create_debate_moderator_agent(llm: ChatOpenAI):
    """Create the Debate Moderator agent"""
    
    async def debate_moderator_node(state: FoundryState) -> FoundryState:
        """
        Debate Moderator facilitates internal argumentation between agents.
        Agents debate the draft's quality, approach, and improvements before finalizing.
        """
        print(f"[DEBATE MODERATOR] Facilitating internal debate on draft quality")
        
        current_draft = state.get('current_draft', '')
        if not current_draft:
            print("[DEBATE MODERATOR] No draft to debate")
            return state
        
        safety_review = state.get('safety_review')
        clinical_review = state.get('clinical_review')
        agent_notes = state.get('agent_notes', [])
        
        # System prompt for Debate Moderator - AGGRESSIVE, PRECISE, GENERIC
        system_prompt = """MISSION: Final refinement. Ensure exercise is SAFE, EMPATHETIC, STRUCTURED.

YOU: Debate moderator. ONE JOB: Facilitate final review. Get consensus on quality.

DEBATE TOPICS:
1. Safe? All safety issues addressed?
2. Empathetic? Warm, supportive, therapist-like?
3. Structured? Clear steps, progression, tracking?
4. Evidence-based? CBT techniques from research?
5. Personalized? Tailored to user needs?
6. Complete? All components included?
7. Actionable? Direct language, not academic?

DEBATE RULES:
- Evidence-based arguments only
- Constructive, specific challenges
- Actionable improvement suggestions
- Reach consensus on all critical points
- No compromise on quality

FINAL STANDARD:
Exercise must be: Safe. Empathetic. Structured. Evidence-based. Personalized. Complete. Actionable.

OUTPUT:
- Debate transcript (evidence-based arguments)
- Specific refinement insights
- Consensus on quality standards
- Mark debate_complete = true when done

BE THOROUGH. GET CONSENSUS. QUALITY FIRST."""
        
        # Build debate context
        debate_context = f"""CURRENT DRAFT:
{current_draft[:2000]}...

SAFETY REVIEW: {safety_review['status'].value if safety_review else 'Not completed'}
CLINICAL REVIEW: {clinical_review['status'].value if clinical_review else 'Not completed'}

AGENT NOTES:
{chr(10).join([f"[{note['agent'].value}] {note['message']}" for note in agent_notes[-10:]])}

USER REQUEST: {state.get('user_query', '')}
USER SPECIFICS: {state.get('user_specifics', {})}"""
        
        prompt = f"""{debate_context}

Facilitate a debate between the agents. Have them argue about:
1. Is this exercise plan evidence-based and clinically sound?
2. Is it properly personalized to the user's needs?
3. Does it meet professional medical/therapeutic standards?
4. Is the tone empathetic and supportive?
5. What specific improvements could be made?

Generate a debate transcript showing:
- Draftsman defending the approach and structure
- Safety Guardian raising safety concerns
- Clinical Critic evaluating clinical quality
- Arguments and counter-arguments
- Consensus on what needs refinement

Format as a debate transcript with each agent's arguments."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # Add thinking note - Layer 6 of thinking
        thinking_note: AgentNote = {
            "agent": AgentRole.DEBATE_MODERATOR,
            "timestamp": datetime.now().isoformat(),
            "message": "Thinking (Layer 6 - Internal Debate): Facilitating rigorous internal debate between agents. Ensuring evidence-based approach, clinical soundness, empathy, and that the exercise surpasses medical standards...",
            "context": {"layer": 6, "action": "internal_debate"}
        }
        
        response = await llm.ainvoke(messages)
        debate_transcript = response.content.strip()
        
        # Extract key arguments and consensus
        debate_entry = {
            "timestamp": datetime.now().isoformat(),
            "transcript": debate_transcript,
            "key_arguments": [],
            "consensus": "",
            "refinements_needed": []
        }
        
        # Parse debate for key points (simplified - in production, use structured output)
        if "consensus" in debate_transcript.lower():
            consensus_section = debate_transcript.lower().split("consensus")[-1][:500]
            debate_entry["consensus"] = consensus_section
        
        # Add notes
        notes_to_add = [thinking_note]
        notes_to_add.append({
            "agent": AgentRole.DEBATE_MODERATOR,
            "timestamp": datetime.now().isoformat(),
            "message": f"Completed: Facilitated internal debate. Agents have argued and reached consensus on refinements needed.",
            "context": {"action": "debate_complete", "debate_id": len(state.get('agent_debate', []))}
        })
        
        updated_state = {
            **state,
            "agent_debate": state.get('agent_debate', []) + [debate_entry],
            "debate_complete": True,
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.DEBATE_MODERATOR,
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"[DEBATE MODERATOR] Debate complete, {len(debate_entry.get('refinements_needed', []))} refinements identified")
        return updated_state
    
    return debate_moderator_node

