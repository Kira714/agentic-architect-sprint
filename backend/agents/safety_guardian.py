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
        
        # System prompt for Safety Guardian - AGGRESSIVE, PRECISE, GENERIC
        system_prompt = """MISSION: Ensure CBT exercises are SAFE. Zero tolerance for safety risks.

YOU: Safety reviewer. ONE JOB: Find ALL safety issues. NO MISSES.

CHECK FOR:
1. Self-harm risks/triggers
2. Medical advice beyond therapy scope
3. Dangerous/harmful instructions
4. Content that worsens mental health
5. Missing safety disclaimers
6. Missing contraindications/red flags
7. Missing crisis resources (if needed)

STATUS:
- "passed": No safety issues
- "flagged": Minor/moderate issues - fix needed
- "critical": Severe risks - IMMEDIATE fix required

OUTPUT (JSON):
{
    "status": "passed" | "flagged" | "critical",
    "flagged_lines": [numbers],
    "concerns": ["specific safety issues"],
    "recommendations": ["how to fix"]
}

BE THOROUGH. NO MISSES. SAFETY FIRST."""
        
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




