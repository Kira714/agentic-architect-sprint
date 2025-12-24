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
    """
    Factory function to create the Safety Guardian agent.
    
    Creates and returns a node function that reviews CBT exercise drafts for safety concerns.
    This agent acts as a safety reviewer with zero tolerance for risks. It checks for
    self-harm risks, medical advice beyond therapy scope, dangerous instructions, and
    missing safety disclaimers.
    
    Args:
        llm: The ChatOpenAI instance to use for LLM calls
        
    Returns:
        A node function (safety_guardian_node) that can be used in the LangGraph workflow
    """
    
    async def safety_guardian_node(state: FoundryState) -> FoundryState:
        """
        Safety Guardian node function - reviews drafts for safety concerns.
        
        This function is called by LangGraph when the workflow routes to the Safety Guardian.
        It performs a comprehensive safety review of the current draft, checking for:
        1. Self-harm risks or triggers
        2. Medical advice beyond therapeutic boundaries
        3. Dangerous or harmful instructions
        4. Content that could worsen mental health
        5. Missing safety disclaimers
        6. Missing contraindications or red flags
        7. Missing crisis resources (if needed)
        
        The review returns a SafetyReview with:
        - status: "passed" (no issues), "flagged" (minor/moderate issues), or "critical" (severe risks)
        - flagged_lines: Line numbers with safety concerns
        - concerns: List of specific safety issues found
        - recommendations: How to fix the issues
        
        If critical or flagged issues are found, the Supervisor will route back to Draftsman
        to fix them before proceeding.
        
        Args:
            state: The current FoundryState containing the draft to review
            
        Returns:
            Updated FoundryState with:
            - safety_review: SafetyReview object with status, concerns, and recommendations
            - agent_notes: Notes added by this agent
            - current_agent: Set to SAFETY_GUARDIAN
            - last_updated: Timestamp of this update
            
        Note:
            If no draft exists, returns state unchanged. The state is automatically
            checkpointed by LangGraph after this function completes.
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




