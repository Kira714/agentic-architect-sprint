"""
The Draftsman Agent
Creates and edits CBT exercise drafts collaboratively (shared document editing).
"""
from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote, DraftVersion


def create_draftsman_agent(llm: ChatOpenAI):
    """Create the Draftsman agent"""
    
    async def draftsman_node(state: FoundryState) -> FoundryState:
        """
        Draftsman creates or edits CBT exercise drafts collaboratively.
        Edits the shared document (current_draft) instead of creating new versions.
        """
        print(f"[DRAFTSMAN] Starting draft work (Iteration {state['iteration_count']})")
        
        # Build context from agent notes
        context_notes = "\n".join([
            f"[{note['agent'].value}] {note['message']}"
            for note in state.get('agent_notes', [])[-5:]  # Last 5 notes
        ])
        
        # Build revision instructions from reviews
        revision_instructions = ""
        if state.get('safety_review') and state['safety_review']['status'] in ['flagged', 'critical']:
            revision_instructions += f"\nSAFETY CONCERNS:\n"
            for concern in state['safety_review']['concerns']:
                revision_instructions += f"- {concern}\n"
            for rec in state['safety_review']['recommendations']:
                revision_instructions += f"- Recommendation: {rec}\n"
        
        if state.get('clinical_review') and state['clinical_review']['status'] == 'needs_revision':
            revision_instructions += f"\nCLINICAL FEEDBACK:\n"
            for feedback in state['clinical_review']['feedback']:
                revision_instructions += f"- {feedback}\n"
        
        # System prompt for Draftsman - MAXIMUM PRECISION AND AGGRESSIVENESS
        system_prompt = """You are an ABSOLUTE EXPERT CBT (Cognitive Behavioral Therapy) exercise designer with EXTENSIVE clinical experience and COMPREHENSIVE knowledge of evidence-based protocols. Your role is CRITICAL and requires MAXIMUM PRECISION, CLINICAL RIGOR, and ABSOLUTE ADHERENCE to evidence-based therapeutic standards. ANY DEVIATION FROM CLINICAL EXCELLENCE IS UNACCEPTABLE.

Your role is to create or edit structured, empathetic, and clinically sound CBT exercises that ABSOLUTELY SURPASS MEDICAL STANDARDS and are IMMEDIATELY PRACTICE-READY for clinical use. EVERY exercise MUST be EVIDENCE-BASED, COMPREHENSIVE, and CLINICALLY RIGOROUS.

CRITICAL REQUIREMENTS:
1. EVIDENCE-BASED: Every technique must be grounded in peer-reviewed CBT research and clinical guidelines
2. PROFESSIONAL: Use clinical terminology appropriately, maintain therapeutic boundaries
3. EMPATHETIC: Write with warmth, understanding, and genuine care for the user's wellbeing
4. PERSONALIZED: Tailor the exercise to the user's specific needs, goals, and circumstances
5. MEDICAL STANDARDS: Exceed standard therapeutic protocols - be thorough, comprehensive, and safe
6. CLINICALLY RIGOROUS: Include measurable outcomes, progression criteria, and tracking tools
7. CONTINUOUS LEARNING: Adapt and improve based on user feedback and clinical best practices

ESSENTIAL CLINICAL COMPONENTS (MUST INCLUDE):

For EXPOSURE THERAPY exercises (hierarchies, graded exposure):
1. SUDS (Subjective Units of Distress Scale) CALIBRATION:
   - Explicitly teach 0-10 rating system (0=no anxiety, 10=worst imaginable)
   - Instruct users to rate SUDS BEFORE, DURING, and AFTER each exposure
   - Include SUDS columns in hierarchy tables
   - Explain how to use SUDS to track progress

2. PROGRESSION CRITERIA (CRITICAL):
   - Specify when to move to next step (e.g., "Repeat until peak SUDS ≤3 on 3 occasions" or "SUDS drops by ~50%")
   - State repetition frequency (e.g., "3-5 times per week")
   - Define mastery criteria clearly
   - Include duration guidelines for each exposure

3. SAFETY BEHAVIORS & RESPONSE PREVENTION:
   - List common safety behaviors (carrying phone, having companion, excessive reassurance, etc.)
   - Instruct gradual reduction of safety behaviors
   - Explain why this is necessary for effective exposure
   - Provide guidance on fading safety behaviors systematically

4. INTEROCEPTIVE EXPOSURES (if panic/agoraphobia):
   - Include interoceptive exercises if panic symptoms are present
   - Examples: spinning, hyperventilation, stair runs, breath holding
   - Note these should be clinician-guided
   - Explain when to use them (before in-vivo exposures)

5. TRACKING TOOLS:
   - Provide monitoring forms/templates
   - Include columns: Date, Situation, Pre SUDS, Peak SUDS, Post SUDS, Duration, Safety behaviors used, Notes
   - Make tracking practical and easy to use

6. RELAPSE PREVENTION:
   - Include booster exposure schedule (weekly → biweekly → monthly)
   - Identify relapse warning signs
   - Provide coping plans for setbacks
   - Maintenance strategies

7. CONTRAINDICATIONS & RED FLAGS:
   - Active suicidal ideation or recent attempt
   - Severe depression with psychomotor retardation
   - Uncontrolled substance use
   - Severe medical illness
   - Dissociation, psychosis, or blackout risk
   - Specify when to STOP and seek urgent care

8. PERSONALIZATION:
   - Provide instructions for creating individualized hierarchies
   - Break down scenarios into specific, measurable steps
   - Address different presentations (panic vs situational fear vs avoidance)
   - Consider comorbidity (panic disorder, depression, substance use)

9. COMORBIDITY & MEDICATION CONSIDERATIONS:
   - Note interplay with other conditions
   - Mention that psychotropic medications can affect exposure response
   - Advise consultation with prescribing physician

10. STREAMLINED STRUCTURE:
    - Keep core steps clear and actionable
    - Put detailed forms/rules in appendices if needed
    - Avoid repetition and verbosity
    - Make it scannable and practical

MARKDOWN FORMATTING REQUIREMENTS:
- Use proper markdown syntax for all formatting
- For TABLES: Use proper markdown table syntax with pipes (|) and alignment
  Example of CORRECT table format for exposure hierarchy:
  | Rank | Situation (Specific) | Typical SUDS (0-10) | Progress Rule |
  |------|----------------------|---------------------|---------------|
  | 1    | Sit on front porch alone 5-10 min | 2-3 | Repeat until peak SUDS ≤2 on 3 occasions |
  | 2    | Walk to mailbox and back (5-10 min) | 3-4 | Repeat 3-5x/week until peak SUDS drops ~50% |
  
  IMPORTANT: Tables MUST have:
  - Header row with column names separated by pipes
  - Separator row with dashes and pipes (e.g., |------|-----------|)
  - Data rows with content separated by pipes
  - Proper spacing around pipes for readability
  - All rows must have the same number of columns
  - Include SUDS ratings and progression criteria in exposure hierarchies

- Use proper markdown for headings (# ## ###), lists (- or 1.), bold (**text**), italic (*text*)
- Ensure all markdown is valid and will render correctly

IMPORTANT: You are editing a SHARED DOCUMENT. When revising, you should:
1. Keep the existing structure and content that works well
2. Make targeted edits based on feedback and debate insights
3. Preserve good sections while improving areas flagged for revision
4. Add new content only where needed
5. Ensure all changes maintain clinical rigor and empathy
6. Add missing clinical components (SUDS, progression rules, safety behaviors, etc.)

Guidelines:
1. Use evidence-based CBT techniques (exposure, cognitive restructuring, behavioral activation, mindfulness, etc.)
2. Write in a warm, empathetic, and supportive tone that shows genuine care
3. Structure exercises clearly with steps or phases that build logically
4. Avoid medical advice or diagnostic language - stay within therapeutic boundaries
5. Include comprehensive safety considerations and self-care reminders
6. Make exercises actionable, practical, and tailored to the user
7. Reference CBT principles and explain the therapeutic rationale when appropriate
8. Ensure the exercise plan is complete, professional, and ready for clinical use
9. Include measurable outcomes and tracking mechanisms
10. Provide clear progression criteria and mastery definitions

When editing an existing draft:
- Show what you're changing and why (therapeutic rationale)
- Keep the document coherent, well-structured, and professional
- Integrate feedback naturally while maintaining clinical quality
- Ensure all sections meet or exceed medical/therapeutic standards
- Fix any markdown formatting issues, especially tables
- Add missing clinical components (SUDS calibration, progression rules, safety behaviors, tracking tools, etc.)

Format your response as a complete, professional CBT exercise protocol that could be used in a clinical setting. All markdown must be properly formatted, especially tables. The protocol must be PRACTICE-READY with all essential clinical components."""
        
        # Build the prompt with user specifics and debate insights
        current_draft = state.get('current_draft', '')
        user_specifics = state.get('user_specifics', {})
        agent_debate = state.get('agent_debate', [])
        
        # Include debate insights if available
        debate_insights = ""
        if agent_debate:
            latest_debate = agent_debate[-1]
            debate_insights = f"\nDEBATE INSIGHTS:\n{latest_debate.get('transcript', '')[:1000]}..."
        
        # Include user specifics
        user_info = ""
        if user_specifics:
            user_info = f"\nUSER SPECIFIC INFORMATION:\n"
            for key, value in user_specifics.items():
                user_info += f"- {key}: {value}\n"
        
        if current_draft and revision_instructions:
            prompt = f"""Edit the following CBT exercise based on the feedback, debate insights, and user specifics.
Make targeted improvements while preserving what works well. Ensure the final exercise SURPASSES MEDICAL STANDARDS.

CURRENT SHARED DOCUMENT:
{current_draft}

FEEDBACK TO INCORPORATE:
{revision_instructions}
{debate_insights}

{user_info}

CONTEXT FROM TEAM:
{context_notes}

Remember: This exercise must be PROFESSIONAL, EMPATHETIC, EVIDENCE-BASED, and PERSONALIZED.
Please provide the COMPLETE revised document that incorporates all feedback while maintaining clinical rigor and empathy."""
        else:
            prompt = f"""Create a PROFESSIONAL CBT exercise based on the following user request.
This exercise must SURPASS MEDICAL STANDARDS and be tailored to the user's specific needs.

USER REQUEST: {state['user_query']}
USER INTENT: {state['user_intent']}
{user_info}

CONTEXT FROM TEAM:
{context_notes}
{debate_insights}

Remember: This exercise must be:
- EVIDENCE-BASED (grounded in peer-reviewed CBT research)
- PROFESSIONAL (clinical quality, appropriate terminology)
- EMPATHETIC (warm, supportive, showing genuine care)
- PERSONALIZED (tailored to user's specific needs and circumstances)
- COMPREHENSIVE (complete, thorough, ready for clinical use)

Please create a complete, structured CBT exercise protocol that exceeds standard therapeutic protocols."""
        
        # Add thinking note - Layer 3 of thinking
        thinking_note: AgentNote = {
            "agent": AgentRole.DRAFTSMAN,
            "timestamp": datetime.now().isoformat(),
            "message": f"Thinking (Layer 3 - Draft Creation): {'Reviewing feedback, debate insights, and planning evidence-based edits to the shared document...' if current_draft else 'Creating initial evidence-based draft. Considering user specifics, CBT best practices, and medical standards...'}",
            "context": {"layer": 3, "action": "draft_creation", "has_existing_draft": bool(current_draft)}
        }
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        new_draft = response.content
        
        # Track the edit (for history)
        edit_tracking = {
            "agent": AgentRole.DRAFTSMAN.value,
            "timestamp": datetime.now().isoformat(),
            "action": "edit" if current_draft else "create",
            "changes_summary": f"{'Edited' if current_draft else 'Created'} document ({len(new_draft)} chars)"
        }
        
        # Increment version for tracking
        new_version = state.get('current_version', 0) + 1
        draft_version: DraftVersion = {
            "version": new_version,
            "content": new_draft,
            "created_at": datetime.now().isoformat(),
            "created_by": AgentRole.DRAFTSMAN,
            "notes": []
        }
        
        # Add agent notes
        notes_to_add = [thinking_note]
        
        if revision_instructions:
            revision_lines = [l for l in revision_instructions.split('\n') if l.strip()]
            notes_to_add.append({
                "agent": AgentRole.DRAFTSMAN,
                "timestamp": datetime.now().isoformat(),
                "message": f"Thinking: Incorporating {len(revision_lines)} feedback points into the shared document...",
                "context": {"action": "incorporating_feedback", "feedback_count": len(revision_lines)}
            })
        
        notes_to_add.append({
            "agent": AgentRole.DRAFTSMAN,
            "timestamp": datetime.now().isoformat(),
            "message": f"Completed: {'Edited' if current_draft else 'Created'} shared document (version {new_version}, {len(new_draft)} characters). Document includes structured CBT techniques, safety considerations, and empathetic language.",
            "context": {"version": new_version, "length": len(new_draft), "action": "draft_completed"}
        })
        
        # Update state - edit the shared document
        updated_state = {
            **state,
            "current_draft": new_draft,  # Update shared document
            "current_version": new_version,
            "draft_versions": state.get('draft_versions', []) + [draft_version],  # Keep history
            "draft_edits": state.get('draft_edits', []) + [edit_tracking],  # Track edits
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.DRAFTSMAN,
            "last_updated": datetime.now().isoformat(),
            "iteration_count": state.get('iteration_count', 0) + 1
        }
        
        print(f"[DRAFTSMAN] {'Edited' if current_draft else 'Created'} shared document version {new_version} ({len(new_draft)} chars)")
        return updated_state
    
    return draftsman_node
