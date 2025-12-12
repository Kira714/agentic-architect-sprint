"""
The Information Gatherer Agent
Asks user for specific details needed to create a personalized CBT exercise.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote


def create_information_gatherer_agent(llm: ChatOpenAI):
    """Create the Information Gatherer agent"""
    
    async def information_gatherer_node(state: FoundryState) -> FoundryState:
        """
        Information Gatherer analyzes the user query and determines what specific
        information is needed to create a personalized, professional CBT exercise.
        """
        print(f"[INFORMATION GATHERER] Analyzing user query for information needs")
        
        user_query = state.get('user_query', '')
        user_intent = state.get('user_intent', '')
        user_specifics = state.get('user_specifics', {})
        
        # System prompt for Information Gatherer
        system_prompt = """You are a PRECISION-CRITICAL clinical information gatherer for Cognitive Behavioral Therapy (CBT) exercise design. You possess EXTENSIVE knowledge of evidence-based CBT terminology, protocols, and clinical decision-making frameworks. Your role requires MAXIMUM CONTEXT-AWARENESS and STRICT ADHERENCE to evidence-based protocols.

MANDATORY PRINCIPLES:
1. ALL decisions MUST be grounded in peer-reviewed CBT research and clinical guidelines
2. Context analysis MUST be COMPREHENSIVE and PRECISE
3. Questions MUST ONLY be asked when ABSOLUTELY NECESSARY for personalization
4. Standard CBT protocols MUST be recognized and executed WITHOUT unnecessary questioning
5. NO questions for well-established, evidence-based CBT exercises with specific conditions

CRITICAL CONTEXT-AWARE DECISION LOGIC:

SCENARIO 1: SPECIFIC CBT EXERCISE REQUEST (NO QUESTIONS NEEDED)
Examples:
- "Create an exposure hierarchy for agoraphobia"
- "I need a thought record exercise for anxiety"
- "Create a behavioral activation plan for depression"
- "Give me a cognitive restructuring exercise for social anxiety"

These are STANDARD, EVIDENCE-BASED CBT PROTOCOLS. You know:
- Exposure hierarchy for agoraphobia follows established protocols (identify triggers, rank by anxiety, gradual exposure)
- Thought records follow standard CBT structure (situation, thought, emotion, evidence, alternative)
- Behavioral activation has proven frameworks
- Cognitive restructuring uses established techniques

→ NO QUESTIONS NEEDED. These exercises can be created using evidence-based best practices for the condition.

SCENARIO 2: EMOTIONAL/FEELING-BASED REQUEST (QUESTIONS NEEDED)
Examples:
- "I'm feeling really anxious and overwhelmed, I need CBT help"
- "I've been struggling with panic attacks and don't know what to do"
- "I feel depressed and want CBT treatment"
- "I'm having trouble with my anxiety, can you help me?"

These indicate:
- User is expressing feelings/emotions
- User wants personalized treatment, not a specific exercise
- User's situation needs to be understood to determine the right CBT approach
- Personalization is essential for effectiveness

→ ASK 2-3 ESSENTIAL QUESTIONS to understand:
  - What specific symptoms or situations are they experiencing?
  - What type of CBT exercise would be most helpful for their situation?
  - Any relevant context (severity, triggers, goals)?

SCENARIO 3: VAGUE OR UNCLEAR REQUEST (1-2 CLARIFYING QUESTIONS)
Examples:
- "Help me with CBT"
- "I need therapy exercises"
- "Create something for my mental health"

→ ASK 1-2 questions to understand what they need.

SCENARIO 4: PERSONAL DETAILS PROVIDED (MAYBE 1-2 QUESTIONS)
Examples:
- "I have severe agoraphobia, can't leave home, tried therapy before"
- "I'm dealing with panic attacks when I go to stores"

If they provide personal details BUT also specify the exercise type → NO QUESTIONS (proceed with standard protocol)
If they provide personal details BUT request general help → ASK 1-2 questions to determine best exercise type

MANDATORY DECISION FRAMEWORK:
- SPECIFIC CBT EXERCISE REQUEST (e.g., "exposure hierarchy for agoraphobia") = EVIDENCE-BASED STANDARD PROTOCOL = ZERO QUESTIONS REQUIRED
- EMOTIONAL/FEELING-BASED REQUEST (e.g., "I'm feeling anxious, help me") = REQUIRES PERSONALIZATION = ASK 2-3 ESSENTIAL QUESTIONS
- VAGUE REQUEST (e.g., "help me with CBT") = REQUIRES CLARIFICATION = ASK 1-2 CLARIFYING QUESTIONS

CONTEXT-AWARENESS REQUIREMENTS:
- You MUST recognize ALL standard CBT exercise types and their evidence-based protocols
- You MUST distinguish between requests requiring personalization vs standard protocols
- You MUST understand CBT terminology with CLINICAL PRECISION
- You MUST avoid unnecessary questioning that delays evidence-based intervention

RESPONSE REQUIREMENTS:
- If NO questions needed: Respond with "No additional questions needed. This is a standard CBT exercise that can be created using evidence-based protocols."
- If questions needed: Provide 2-3 ESSENTIAL, EMPATHETIC, PROFESSIONALLY-FRAMED questions
- ALL questions MUST be clinically relevant and necessary for personalization
- NO generic or redundant questions permitted"""
        
        prompt = f"""Analyze the following user request with CONTEXT-AWARENESS about CBT terminology and protocols.

USER REQUEST: {user_query}
USER INTENT: {user_intent}
ALREADY COLLECTED: {user_specifics}

CONTEXT ANALYSIS - Determine which scenario applies:

SCENARIO 1: SPECIFIC CBT EXERCISE REQUEST
Look for specific CBT exercise types:
- "exposure hierarchy", "exposure therapy", "graded exposure"
- "thought record", "thought challenging", "cognitive restructuring"
- "behavioral activation", "activity scheduling"
- "mindfulness exercise", "breathing exercise"
- "CBT protocol for [condition]"
- "CBT exercise for [condition]"

If the request contains a SPECIFIC CBT EXERCISE TYPE + CONDITION:
→ NO QUESTIONS NEEDED. These are standard, evidence-based protocols you can create.

SCENARIO 2: EMOTIONAL/FEELING-BASED REQUEST
Look for emotional language:
- "I'm feeling...", "I feel...", "I'm struggling with..."
- "I need help with...", "I want treatment for..."
- Emotional expressions without specifying exercise type

If the user expresses FEELINGS/EMOTIONS and wants CBT HELP (not a specific exercise):
→ ASK 2-3 ESSENTIAL QUESTIONS to understand their situation and determine the right CBT approach.

SCENARIO 3: VAGUE REQUEST
- Generic requests like "help me", "CBT exercises", "therapy"
→ ASK 1-2 CLARIFYING QUESTIONS.

SCENARIO 4: PERSONAL DETAILS + SPECIFIC EXERCISE
- "I have [condition], create [specific exercise] for it"
→ NO QUESTIONS (they specified the exercise, proceed with standard protocol)

- "I have [condition], I need CBT help"
→ ASK 1-2 questions to determine which exercise type would help

Respond in this format:
1. First, identify the SCENARIO (1, 2, 3, or 4) and explain your reasoning
2. If Scenario 1 or 4 (specific exercise): "No additional questions needed. This is a standard CBT exercise that can be created using evidence-based protocols."
3. If Scenario 2 or 3: List 2-3 essential questions:
   QUESTION 1: [essential question]
   QUESTION 2: [essential question]

Remember: Be context-aware. Understand the difference between requesting a specific CBT exercise (no questions) vs expressing feelings and wanting CBT treatment (questions needed)."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # Add thinking note - Layer 2 of thinking
        thinking_note: AgentNote = {
            "agent": AgentRole.INFORMATION_GATHERER,
            "timestamp": datetime.now().isoformat(),
            "message": "Thinking (Layer 2 - Information Gathering): Analyzing user request with context awareness. Determining if this is a standard CBT exercise (no questions) vs emotional/personal request (questions needed)...",
            "context": {"layer": 2, "action": "information_analysis"}
        }
        
        response = await llm.ainvoke(messages)
        response_content = response.content.strip()
        
        # Parse questions from response
        questions = []
        lines = response_content.split('\n')
        for line in lines:
            if 'QUESTION' in line.upper() and ':' in line:
                question = line.split(':', 1)[1].strip()
                if question:
                    questions.append(question)
        
        # Check if information is sufficient
        information_sufficient = len(questions) == 0 or "no additional questions needed" in response_content.lower()
        
        # Add notes
        notes_to_add = [thinking_note]
        
        if information_sufficient:
            notes_to_add.append({
                "agent": AgentRole.INFORMATION_GATHERER,
                "timestamp": datetime.now().isoformat(),
                "message": "Completed: User request contains sufficient information. Proceeding to create exercise plan.",
                "context": {"action": "sufficient_info", "questions_count": 0}
            })
        else:
            notes_to_add.append({
                "agent": AgentRole.INFORMATION_GATHERER,
                "timestamp": datetime.now().isoformat(),
                "message": f"Thinking: Identified {len(questions)} areas where more information would help create a better exercise plan. Preparing empathetic questions...",
                "context": {"action": "preparing_questions", "questions_count": len(questions)}
            })
            notes_to_add.append({
                "agent": AgentRole.INFORMATION_GATHERER,
                "timestamp": datetime.now().isoformat(),
                "message": f"Completed: Prepared {len(questions)} professional, empathetic questions to gather essential information.",
                "context": {"action": "questions_ready", "questions": questions}
            })
        
        updated_state = {
            **state,
            "questions_for_user": questions if not information_sufficient else [],
            "information_gathered": information_sufficient,
            "awaiting_user_response": not information_sufficient,
            "is_halted": not information_sufficient,  # Halt workflow if we need user input
            "awaiting_human_approval": not information_sufficient,  # Signal that we need user response
            "agent_notes": state.get('agent_notes', []) + notes_to_add,
            "current_agent": AgentRole.INFORMATION_GATHERER,
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"[INFORMATION GATHERER] {'Information sufficient' if information_sufficient else f'Prepared {len(questions)} questions - HALTING for user response'}")
        return updated_state
    
    return information_gatherer_node

