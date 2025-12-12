"""
The Context Analyzer Agent
First layer of thinking - analyzes user query for context, intent, and required information.
This is the first of 5-6 thinking layers for deep context awareness.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime
from state import FoundryState, AgentRole, AgentNote


def create_context_analyzer_agent(llm: ChatOpenAI):
    """Create the Context Analyzer agent - Layer 1 of thinking"""
    
    async def context_analyzer_node(state: FoundryState) -> FoundryState:
        """
        Context Analyzer - First thinking layer
        Deeply analyzes user query for:
        1. Explicit vs implicit intent
        2. Emotional state indicators
        3. Specificity level (standard exercise vs personalized treatment)
        4. Required context for proper response
        """
        print(f"[CONTEXT ANALYZER] Layer 1: Analyzing user query context")
        
        user_query = state.get('user_query', '')
        user_intent = state.get('user_intent', '')
        
        # System prompt for Context Analyzer - Layer 1 thinking
        system_prompt = """You are a Context Analyzer - the PRECISION-CRITICAL first layer of a multi-agent thinking system for Cognitive Behavioral Therapy (CBT) exercise design. Your role requires MAXIMUM CONTEXT-AWARENESS, CLINICAL PRECISION, and EVIDENCE-BASED analysis. You MUST perform COMPREHENSIVE, SYSTEMATIC context analysis with CLINICAL RIGOR.

MANDATORY ANALYSIS PROTOCOL (THINKING LAYER 1):

1. EXPLICIT INTENT ANALYSIS (REQUIRED):
   - Identify PRECISELY what the user explicitly requested
   - Categorize: Specific CBT exercise (e.g., "exposure hierarchy", "thought record") vs General help request vs Emotional expression
   - Determine EXACT exercise type and condition if specified
   - NO assumptions - base analysis STRICTLY on explicit language

2. IMPLICIT INTENT ANALYSIS (REQUIRED):
   - Infer CLINICALLY what the user likely needs based on evidence-based CBT protocols
   - Distinguish: Standard evidence-based protocol vs Personalized treatment requiring additional information
   - Determine: Information request vs Exercise request vs Emotional support request
   - Apply CLINICAL REASONING based on CBT knowledge

3. EMOTIONAL STATE ASSESSMENT (REQUIRED):
   - Identify ALL emotional indicators with CLINICAL PRECISION
   - Analyze: Emotional language patterns, distress signals, urgency indicators, coping level indicators
   - Assess: Severity, intensity, and clinical presentation indicators
   - Apply EVIDENCE-BASED emotional assessment frameworks

4. SPECIFICITY LEVEL CLASSIFICATION (MANDATORY):
   - HIGH: Specific CBT exercise type + condition (e.g., "exposure hierarchy for agoraphobia") = Standard protocol
   - MEDIUM: Condition mentioned but exercise type unspecified = May require clarification
   - LOW: Vague request (e.g., "help me with anxiety") = Requires information gathering

5. CONTEXT REQUIREMENTS DETERMINATION (CRITICAL):
   - Determine if personalization is REQUIRED (emotional requests = yes, specific exercises = no)
   - Identify SPECIFIC information that would enhance therapeutic effectiveness
   - Assess if this is a standard evidence-based protocol that can be created immediately
   - Apply CLINICAL DECISION-MAKING frameworks

Respond with a structured analysis in this format:
CONTEXT ANALYSIS:
- Explicit Intent: [what they said]
- Implicit Intent: [what they likely need]
- Emotional State: [indicators found]
- Specificity: [HIGH/MEDIUM/LOW]
- Personalization Needed: [YES/NO and why]
- Recommended Action: [proceed with standard protocol / gather information / provide support]"""
        
        prompt = f"""Perform deep context analysis of this user query:

USER QUERY: {user_query}
USER INTENT: {user_intent}

Analyze all aspects: explicit intent, implicit intent, emotional state, specificity, and context requirements.
Be thorough - this is the foundation for all subsequent thinking layers."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # Add thinking note
        thinking_note: AgentNote = {
            "agent": AgentRole.SUPERVISOR,  # Using supervisor role for now, could add new role
            "timestamp": datetime.now().isoformat(),
            "message": "Thinking (Layer 1 - Context Analysis): Analyzing user query for explicit intent, implicit needs, emotional state, and specificity level...",
            "context": {"layer": 1, "action": "context_analysis"}
        }
        
        response = await llm.ainvoke(messages)
        context_analysis = response.content.strip()
        
        # Store context analysis in state for other agents
        updated_state = {
            **state,
            "agent_notes": state.get('agent_notes', []) + [thinking_note],
            "adaptation_notes": state.get('adaptation_notes', []) + [f"Context Analysis (Layer 1): {context_analysis[:200]}..."],
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"[CONTEXT ANALYZER] Layer 1 analysis complete")
        return updated_state
    
    return context_analyzer_node

