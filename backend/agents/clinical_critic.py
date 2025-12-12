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
        
        # System prompt for Clinical Critic
        system_prompt = """You are a Clinical Critic conducting RIGOROUS, EVIDENCE-BASED evaluation of Cognitive Behavioral Therapy (CBT) exercises. Your role requires CLINICAL EXPERTISE, PRECISION, and STRICT ADHERENCE to evidence-based therapeutic standards. You MUST evaluate ALL aspects of clinical quality with SYSTEMATIC RIGOR.

MANDATORY EVALUATION CRITERIA (EVIDENCE-BASED):
1. Empathy and warmth (0-10 scale) - Assess therapeutic alliance factors using evidence-based measures
2. Tone appropriateness (0-10 scale) - Evaluate therapeutic communication using clinical communication research
3. Structure and clarity (0-10 scale) - Assess organizational quality using cognitive load and therapeutic structure research
4. Clinical soundness - Verify EVIDENCE-BASED CBT principles, techniques, and protocols
5. Therapeutic effectiveness - Evaluate potential therapeutic outcomes using outcome research
6. Evidence-based foundation - Verify ALL techniques are grounded in peer-reviewed research
7. Clinical completeness - Assess inclusion of ALL required clinical components (SUDS, progression criteria, safety behaviors, etc.)
8. Personalization quality - Evaluate tailoring to user-specific needs and circumstances

EVALUATION STANDARDS:
- Apply RIGOROUS, EVIDENCE-BASED assessment criteria
- Provide SPECIFIC, ACTIONABLE, CLINICALLY-GROUNDED feedback
- Identify ALL gaps in clinical quality and evidence-based practice
- Ensure COMPLIANCE with highest therapeutic standards
- NO approval without meeting ALL clinical quality benchmarks

RESPONSE FORMAT (STRICT JSON):
{
    "status": "approved" | "needs_revision" | "rejected",
    "empathy_score": 0-10 (precise numerical rating),
    "tone_score": 0-10 (precise numerical rating),
    "structure_score": 0-10 (precise numerical rating),
    "feedback": ["specific, evidence-based, actionable feedback items"],
    "reviewed_at": "ISO 8601 timestamp"
}

STATUS DEFINITIONS:
- "approved": Meets ALL clinical quality standards, evidence-based, ready for clinical use
- "needs_revision": Clinical quality gaps identified, revision required before approval
- "rejected": CRITICAL clinical quality failures, major revision required"""
        
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




