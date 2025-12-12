"""
The Clinical Critic Agent
Evaluates tone, empathy, and clinical appropriateness.
"""
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote, ClinicalReview, ClinicalStatus


def create_clinical_critic_agent(llm: ChatOpenAI):
    """Create the Clinical Critic agent"""
    
    async def clinical_critic_node(state: FoundryState) -> FoundryState:
        """
        Clinical Critic evaluates drafts for tone, empathy, and clinical quality.
        """
        print(f"[CLINICAL CRITIC] Reviewing draft for clinical quality")
        
        if not state.get('current_draft'):
            print("[CLINICAL CRITIC] No draft to review")
            return state
        
        draft = state['current_draft']
        
        # System prompt for Clinical Critic - AGGRESSIVE, PRECISE, GENERIC
        system_prompt = """MISSION: Ensure CBT exercises are EMPATHETIC and STRUCTURED. Evaluate clinical quality.

YOU: Clinical quality reviewer. ONE JOB: Rate empathy, tone, structure. Find quality gaps.

EVALUATE (0-10 scale each):
1. Empathy: Warm, supportive, therapist-like? Shows genuine care?
2. Tone: Appropriate for CBT? Conversational, not academic?
3. Structure: Clear steps? Progression criteria? Tracking tools? Actionable?

ALSO CHECK:
- Evidence-based CBT techniques?
- Personalized to user needs?
- Complete (all components included)?
- Actionable language (not academic)?

STATUS:
- "approved": Meets all standards, ready to use
- "needs_revision": Quality gaps, fix needed
- "rejected": Major failures, major fix needed

OUTPUT (JSON):
{
    "status": "approved" | "needs_revision" | "rejected",
    "empathy_score": 0-10,
    "tone_score": 0-10,
    "structure_score": 0-10,
    "feedback": ["specific, actionable feedback"],
    "reviewed_at": "ISO timestamp"
}

BE STRICT. NO COMPROMISES. QUALITY MATTERS."""
        
        prompt = f"""Evaluate the following CBT exercise for clinical quality:

{draft}

Assess the empathy, tone, structure, and overall therapeutic value.
Provide specific, actionable feedback."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Parse response
        import json
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content:
                json_str = content[content.index("{"):content.rindex("}")+1]
            else:
                json_str = content
            
            review_data = json.loads(json_str)
        except:
            review_data = {
                "status": "needs_revision",
                "empathy_score": 5.0,
                "tone_score": 5.0,
                "structure_score": 5.0,
                "feedback": ["Unable to parse clinical review. Manual review recommended."]
            }
        
        # Create clinical review
        clinical_review: ClinicalReview = {
            "status": ClinicalStatus(review_data.get("status", "needs_revision")),
            "empathy_score": float(review_data.get("empathy_score", 5.0)),
            "tone_score": float(review_data.get("tone_score", 5.0)),
            "structure_score": float(review_data.get("structure_score", 5.0)),
            "feedback": review_data.get("feedback", []),
            "reviewed_at": datetime.now().isoformat()
        }
        
        # Add detailed agent notes
        notes_to_add = []
        avg_score = (clinical_review['empathy_score'] + clinical_review['tone_score'] + clinical_review['structure_score']) / 3
        
        notes_to_add.append({
            "agent": AgentRole.CLINICAL_CRITIC,
            "timestamp": datetime.now().isoformat(),
            "message": f"Thinking (Layer 5 - Clinical Review): Evaluating clinical quality: assessing evidence-based techniques, empathy, tone, structure, therapeutic effectiveness, and medical standards compliance...",
            "context": {"layer": 5, "action": "clinical_evaluation"}
        })
        
        if clinical_review['status'] == ClinicalStatus.APPROVED:
            notes_to_add.append({
                "agent": AgentRole.CLINICAL_CRITIC,
                "timestamp": datetime.now().isoformat(),
                "message": f"Clinical review APPROVED. Excellent quality scores: Empathy {clinical_review['empathy_score']:.1f}/10, Tone {clinical_review['tone_score']:.1f}/10, Structure {clinical_review['structure_score']:.1f}/10. Average: {avg_score:.1f}/10",
                "context": {
                    "status": clinical_review['status'].value,
                    "scores": {
                        "empathy": clinical_review['empathy_score'],
                        "tone": clinical_review['tone_score'],
                        "structure": clinical_review['structure_score']
                    }
                }
            })
        elif clinical_review['status'] == ClinicalStatus.NEEDS_REVISION:
            notes_to_add.append({
                "agent": AgentRole.CLINICAL_CRITIC,
                "timestamp": datetime.now().isoformat(),
                "message": f"Clinical review: NEEDS REVISION. Scores: Empathy {clinical_review['empathy_score']:.1f}/10, Tone {clinical_review['tone_score']:.1f}/10, Structure {clinical_review['structure_score']:.1f}/10. Average: {avg_score:.1f}/10. Providing {len(clinical_review['feedback'])} feedback points.",
                "context": {
                    "status": clinical_review['status'].value,
                    "scores": {
                        "empathy": clinical_review['empathy_score'],
                        "tone": clinical_review['tone_score'],
                        "structure": clinical_review['structure_score']
                    },
                    "feedback_count": len(clinical_review['feedback'])
                }
            })
        else:
            notes_to_add.append({
                "agent": AgentRole.CLINICAL_CRITIC,
                "timestamp": datetime.now().isoformat(),
                "message": f"Clinical review REJECTED. Quality scores too low. Average: {avg_score:.1f}/10. Significant revision needed.",
                "context": {
                    "status": clinical_review['status'].value,
                    "scores": {
                        "empathy": clinical_review['empathy_score'],
                        "tone": clinical_review['tone_score'],
                        "structure": clinical_review['structure_score']
                    }
                }
            })
        
        note = notes_to_add[-1]  # Keep for backward compatibility
        
        updated_state = {
            **state,
            "clinical_review": clinical_review,
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.CLINICAL_CRITIC,
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"[CLINICAL CRITIC] Review complete: {clinical_review['status'].value} (Avg: {avg_score:.1f}/10)")
        
        return updated_state
    
    return clinical_critic_node




