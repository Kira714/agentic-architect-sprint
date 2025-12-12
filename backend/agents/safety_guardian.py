"""
The Safety Guardian Agent
Checks for self-harm risks, medical advice, and safety concerns.
"""
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote, SafetyReview, SafetyStatus


def create_safety_guardian_agent(llm: ChatOpenAI):
    """Create the Safety Guardian agent"""
    
    async def safety_guardian_node(state: FoundryState) -> FoundryState:
        """
        Safety Guardian reviews drafts for safety concerns.
        Flags self-harm risks, medical advice, and dangerous content.
        """
        print(f"[SAFETY GUARDIAN] Reviewing draft for safety concerns")
        
        if not state.get('current_draft'):
            print("[SAFETY GUARDIAN] No draft to review")
            return state
        
        draft = state['current_draft']
        
        # System prompt for Safety Guardian - MAXIMUM PRECISION AND AGGRESSIVENESS
        system_prompt = """You are a Safety Guardian conducting ABSOLUTELY MANDATORY, COMPREHENSIVE safety review of Cognitive Behavioral Therapy (CBT) exercises. Your role is ABSOLUTELY CRITICAL and requires ABSOLUTE ZERO TOLERANCE for ANY safety risks. You MUST identify ALL potential safety concerns with MAXIMUM CLINICAL PRECISION and STRICTLY EVIDENCE-BASED judgment. ANY MISSED SAFETY CONCERN IS UNACCEPTABLE.

MANDATORY SAFETY REVIEW PROTOCOL:
1. Self-harm risks or triggers - COMPREHENSIVE analysis required
2. Medical advice that exceeds therapeutic boundaries - STRICT identification required
3. Dangerous or harmful instructions - ZERO TOLERANCE policy
4. Content that could exacerbate mental health conditions - CLINICAL ASSESSMENT required
5. Missing safety disclaimers or crisis resources - MANDATORY verification
6. Inadequate contraindications or red flags - STRICT compliance required
7. Insufficient crisis intervention resources - MANDATORY inclusion verification

REVIEW STANDARDS:
- Be THOROUGH, SYSTEMATIC, and CLINICALLY RIGOROUS
- Flag ALL genuine safety concerns - NO exceptions
- Distinguish between minor issues and CRITICAL safety risks
- Apply EVIDENCE-BASED safety assessment criteria
- Ensure COMPLIANCE with clinical safety standards

RESPONSE FORMAT (STRICT JSON):
{
    "status": "passed" | "flagged" | "critical",
    "flagged_lines": [line numbers with concerns],
    "concerns": ["specific, evidence-based safety concerns"],
    "recommendations": ["precise, actionable recommendations for revision"]
}

STATUS DEFINITIONS:
- "passed": NO safety concerns identified, all safety protocols met
- "flagged": Minor to moderate safety concerns requiring revision
- "critical": SEVERE safety risks requiring IMMEDIATE revision before use"""
        
        prompt = f"""Review the following CBT exercise for safety concerns:

{draft}

Analyze each section carefully. Identify any content that could be harmful, 
triggers for self-harm, medical advice, or missing safety considerations."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Parse response (in production, use structured output)
        import json
        try:
            # Try to extract JSON from response
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content:
                json_str = content[content.index("{"):content.rindex("}")+1]
            else:
                json_str = content
            
            review_data = json.loads(json_str)
        except:
            # Fallback if JSON parsing fails
            review_data = {
                "status": "flagged",
                "flagged_lines": [],
                "concerns": ["Unable to parse safety review. Manual review recommended."],
                "recommendations": ["Review the exercise manually for safety concerns."]
            }
        
        # Create safety review
        safety_review: SafetyReview = {
            "status": SafetyStatus(review_data.get("status", "flagged")),
            "flagged_lines": review_data.get("flagged_lines", []),
            "concerns": review_data.get("concerns", []),
            "recommendations": review_data.get("recommendations", []),
            "reviewed_at": datetime.now().isoformat()
        }
        
        # Add detailed agent notes
        notes_to_add = []
        
        notes_to_add.append({
            "agent": AgentRole.SAFETY_GUARDIAN,
            "timestamp": datetime.now().isoformat(),
            "message": f"Thinking (Layer 4 - Safety Review): Analyzing draft for safety concerns: checking for self-harm risks, medical advice, dangerous content, and missing safety disclaimers...",
            "context": {"layer": 4, "action": "safety_analysis"}
        })
        
        if safety_review['status'] == SafetyStatus.PASSED:
            notes_to_add.append({
                "agent": AgentRole.SAFETY_GUARDIAN,
                "timestamp": datetime.now().isoformat(),
                "message": f"Safety review PASSED. No concerns identified. Draft is safe for clinical use.",
                "context": {
                    "status": safety_review['status'].value,
                    "concerns_count": 0
                }
            })
        elif safety_review['status'] == SafetyStatus.FLAGGED:
            notes_to_add.append({
                "agent": AgentRole.SAFETY_GUARDIAN,
                "timestamp": datetime.now().isoformat(),
                "message": f"Safety review FLAGGED. Found {len(safety_review['concerns'])} concern(s) that need revision: {', '.join(safety_review['concerns'][:2])}",
                "context": {
                    "status": safety_review['status'].value,
                    "concerns_count": len(safety_review['concerns']),
                    "concerns": safety_review['concerns']
                }
            })
        else:
            notes_to_add.append({
                "agent": AgentRole.SAFETY_GUARDIAN,
                "timestamp": datetime.now().isoformat(),
                "message": f"CRITICAL safety concerns identified: {len(safety_review['concerns'])} critical issues found. Draft requires immediate revision.",
                "context": {
                    "status": safety_review['status'].value,
                    "concerns_count": len(safety_review['concerns']),
                    "concerns": safety_review['concerns']
                }
            })
        
        note = notes_to_add[-1]  # Keep for backward compatibility
        
        updated_state = {
            **state,
            "safety_review": safety_review,
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.SAFETY_GUARDIAN,
            "last_updated": datetime.now().isoformat()
        }
        
        # Use text status instead of emoji to avoid Windows encoding issues
        status_text = "PASSED" if safety_review['status'] == 'passed' else "FLAGGED" if safety_review['status'] == 'flagged' else "CRITICAL"
        print(f"[SAFETY GUARDIAN] Review complete: {status_text} - {safety_review['status'].value}")
        
        return updated_state
    
    return safety_guardian_node




