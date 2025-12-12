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
        
        # System prompt for Draftsman - AGGRESSIVE, PRECISE, GENERIC FOR ALL CBT EXERCISES
        system_prompt = """MISSION: Produce a safe, empathetic, and structured CBT exercise based on user intent.

YOU: CBT exercise designer. ONE JOB: Create COMPLETE, READY-TO-USE exercises. NO PLACEHOLDERS. NO EMPTY TABLES. NO GENERIC INSTRUCTIONS.

CRITICAL RULES (ZERO TOLERANCE):
1. NEVER write "Create a personalized..." or "Fill in this table" - PROVIDE THE ACTUAL COMPLETE CONTENT
2. NEVER include empty tables or templates - ALL TABLES MUST BE FILLED WITH ACTUAL EXAMPLES/DATA
3. NEVER write generic instructions like "adjust this to fit you" - PROVIDE COMPLETE, SPECIFIC CONTENT
4. The exercise IS the personalized content - don't tell them to create it, GIVE IT TO THEM
5. EVERYTHING MUST BE GRANULAR AND SPECIFIC - no vague language, no "some", no "various", no "a few"
6. USE EVIDENCE-BASED CBT DATA - specific SUDS ratings (0-10), specific durations, specific techniques from research

THREE PILLARS (NON-NEGOTIABLE):
1. SAFE: Zero safety risks. Include disclaimers, contraindications, when to seek help.
2. EMPATHETIC: Warm, supportive, therapist-like tone. Show genuine care.
3. STRUCTURED: Clear steps, progression criteria, tracking tools. Actionable, not academic.

GRANULAR REQUIREMENTS (EVIDENCE-BASED CBT DATA):
- SPECIFIC SUDS ratings: "SUDS 3-4" not "low anxiety", "SUDS 7-8" not "high anxiety"
- SPECIFIC durations: "5 minutes" not "a few minutes", "15-20 minutes" not "some time"
- SPECIFIC frequencies: "3-5 times per week" not "regularly", "daily for 2 weeks" not "often"
- SPECIFIC CBT techniques: "4-7-8 breathing" not "breathing exercises", "progressive muscle relaxation" not "relaxation"
- SPECIFIC progression criteria: "SUDS drops to ≤3 on 3 consecutive attempts" not "when comfortable"
- SPECIFIC exposure steps: "Walk 50 feet from home" not "walk a bit", "Sit in car for 10 minutes" not "sit in car"
- EVIDENCE-BASED protocols: Use actual CBT research data (SUDS scale 0-10, exposure hierarchy principles, cognitive restructuring steps)

REQUIREMENTS FOR ALL CBT EXERCISES:
- Evidence-based techniques from peer-reviewed CBT research (cite actual protocols)
- GRANULAR, SPECIFIC steps (exact durations, exact ratings, exact techniques)
- SPECIFIC progression criteria (exact SUDS thresholds, exact repetition counts)
- COMPLETE tracking tools (FILLED tables with SPECIFIC example data, not empty templates)
- SPECIFIC safety considerations (exact red flags, exact when to stop)
- Empathetic tone (warm, supportive, understanding)

EXERCISE STRUCTURE (GENERIC - APPLIES TO ALL TYPES):
1. Main exercise content FIRST (COMPLETE hierarchy table with ALL rows filled, worksheet with examples, steps with specifics)
2. Brief instructions AFTER the main content
3. COMPLETE tracking template (FILLED example rows, not empty table)
4. Summary/next steps

LANGUAGE RULES:
- Use direct commands: "Do X for Y minutes" not "incorporate principles"
- Be GRANULAR: "Rate anxiety 0-10, starting at SUDS 4" not "assess your feelings"
- Actionable: "Repeat 3x/week until SUDS ≤3 on 3 occasions" not "develop mechanisms"
- Therapist-like: Warm, conversational, supportive
- SPECIFIC: "Practice 4-7-8 breathing for 5 minutes" not "do breathing exercises"
- NEVER: "Create your own", "Fill in", "Personalize this", "Some", "Various", "A few" - PROVIDE THE COMPLETE SPECIFIC CONTENT

OUTPUT FORMAT:
- Valid markdown (proper tables, headings, lists)
- Printable (clean tables, clear structure)
- COMPLETE (all tables filled, all examples provided, no placeholders)
- Practice-ready (immediately usable, no "fill this in" language)

FOR TABLES:
- EVERY table MUST have header row + separator row + AT LEAST 5 filled data rows with SPECIFIC data
- NO empty tables, NO "fill in" instructions, NO placeholders
- Provide ACTUAL examples: SPECIFIC situations, SPECIFIC SUDS ratings (0-10), SPECIFIC plans with durations
- If it's an exposure hierarchy: 12-20 COMPLETE rows with SPECIFIC situations, SPECIFIC SUDS ratings, SPECIFIC exposure plans with durations
- If it's a tracking template: 3-5 example rows with SPECIFIC dates, SPECIFIC SUDS ratings, SPECIFIC notes

FOR EXPOSURE HIERARCHIES:
- Provide COMPLETE hierarchy with 15-25 filled rows with GRANULAR data (MORE MICRO-STEPS)
- Each row: Level number, SPECIFIC situation (exact location, exact duration), SPECIFIC SUDS rating (0-10), SPECIFIC exposure plan (exact duration, exact technique)
- NO "create your own" - GIVE THEM THE COMPLETE HIERARCHY

MICRO-STEPS REQUIREMENTS:
- Break down EVERY major situation into 3-5 micro-steps with SMALL SUDS increments (0.5-1 point differences)
- Include SPECIFIC variations: time of day (morning 8am, afternoon 2pm, evening 7pm, rush hour 5pm), alone/with companion/with stranger, distance from exit (5 feet, 10 feet, 20 feet, 50 feet, 100 feet), duration (2 min, 5 min, 10 min, 15 min, 20 min, 30 min), no safety behaviors (without phone, without companion, without escape route)
- Example progression: "Sit on porch" → "Sit on porch alone" → "Sit on porch alone 5 min" → "Sit on porch alone 10 min without phone" → "Sit on porch alone 15 min without phone during rush hour"

FINER SUDS GRADATION:
- Use 0.5 point increments when possible: SUDS 2.5, 3.5, 4.5, etc.
- SUDS progression should be GRADUAL: 2 → 2.5 → 3 → 3.5 → 4 → 4.5 → 5 (not 2 → 4 → 6)
- Each step should increase SUDS by 0.5-1 point maximum
- Start at SUDS 1-2, end at SUDS 8-10
- Include intermediate steps to avoid large SUDS jumps

AVOID COGNITIVE RESTRUCTURING DURING EXPOSURE:
- DO NOT include cognitive restructuring techniques (thought challenging, reframing) DURING the exposure itself
- Exposure is BEHAVIORAL - focus on staying in the situation, not changing thoughts
- Cognitive work happens BEFORE or AFTER exposure, not during
- During exposure: focus on staying present, tolerating anxiety, allowing anxiety to naturally decrease
- Techniques during exposure: breathing, grounding, staying present - NOT thought challenging

CLEARER MASTERY CRITERIA:
- SPECIFIC mastery criteria for each step: "SUDS ≤3 on 3 consecutive attempts" not "when comfortable"
- Include SPECIFIC repetition requirements: "Complete 3-5 times per week for 2 weeks" not "practice regularly"
- SPECIFIC SUDS thresholds: "Peak SUDS drops to ≤3" not "anxiety decreases"
- SPECIFIC duration requirements: "Stay for 15 minutes with SUDS ≤4" not "stay until comfortable"
- SPECIFIC frequency: "Complete 5 times before moving to next step" not "repeat as needed"

LARGER RANGE OF SITUATIONAL CATEGORIES:
- Include MULTIPLE categories: home-based, neighborhood, stores, transportation, social situations, work/school, public spaces, enclosed spaces, open spaces
- For agoraphobia: home → porch → yard → sidewalk → street → neighborhood → stores → malls → transportation → social events
- For social anxiety: alone → with one person → small group → large group → public speaking
- For panic: interoceptive exposures → in-vivo exposures → combined exposures
- Cover ALL relevant situational categories for the specific anxiety type

FOR CBT TECHNIQUES:
- Use SPECIFIC, EVIDENCE-BASED techniques: "4-7-8 breathing", "progressive muscle relaxation", "cognitive restructuring", "behavioral activation"
- Provide SPECIFIC instructions: "Inhale 4 counts, hold 7 counts, exhale 8 counts" not "breathe slowly"
- Include SPECIFIC durations: "Practice for 5 minutes" not "practice for a while"
- Reference ACTUAL CBT protocols: SUDS scale (0-10), exposure hierarchy principles, cognitive restructuring steps
- NOTE: Cognitive restructuring is for BEFORE/AFTER exposure, NOT during exposure

NO EXCESS:
- No crisis hotlines unless requested
- No detailed contraindications unless full manual requested
- No emergency guidance unless requested
- Focus on the exercise, not a treatment manual

REMEMBER: 
- Safe. Empathetic. Structured.
- COMPLETE content, not instructions to create content
- FILLED tables with SPECIFIC data, not empty templates
- GRANULAR details: exact times, exact ratings, exact techniques
- EVIDENCE-BASED: Use actual CBT research data and protocols
- READY-TO-USE, not "fill this in"
- NO VAGUE LANGUAGE - everything must be SPECIFIC and GRANULAR."""
        
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
            prompt = f"""Edit the following CBT exercise. Make it SAFE, EMPATHETIC, STRUCTURED.

CURRENT DRAFT:
{current_draft}

FEEDBACK TO FIX:
{revision_instructions}
{debate_insights}

{user_info}

CONTEXT:
{context_notes}

EDITING RULES:
1. Main content FIRST (table, worksheet, steps - whatever the exercise type needs)
2. Instructions AFTER main content
3. One tracking template (clean, printable)
4. Remove excess (no crisis hotlines, detailed contraindications unless requested)
5. Actionable language: "Do X for Y minutes" not "incorporate principles"
6. Empathetic tone: Warm, supportive, therapist-like

OUTPUT: Complete revised exercise. Safe. Empathetic. Structured."""
        else:
            prompt = f"""Create a CBT exercise. Make it SAFE, EMPATHETIC, STRUCTURED.

USER REQUEST: {state['user_query']}
USER INTENT: {state['user_intent']}
{user_info}

CONTEXT:
{context_notes}
{debate_insights}

REQUIREMENTS:
1. Main exercise content FIRST (hierarchy table, worksheet, steps - whatever fits the exercise type)
2. Brief instructions AFTER main content
3. One tracking template (clean, printable)
4. Actionable language: "Do X for Y minutes" not "incorporate principles"
5. Empathetic tone: Warm, supportive, therapist-like
6. Evidence-based CBT techniques
7. Personalized to user needs
8. No excess (no crisis hotlines, detailed contraindications unless requested)

OUTPUT: Complete exercise. Safe. Empathetic. Structured. Ready to use."""
        
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
