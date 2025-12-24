"""
Intent Classifier
Determines user intent and routes to appropriate handler
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Literal
import os
from dotenv import load_dotenv

load_dotenv()

IntentType = Literal["cbt_protocol", "question", "conversation", "unknown"]

async def classify_intent(user_query: str) -> tuple[IntentType, str]:
    """
    Classify user intent and extract reasoning.
    
    This function analyzes a user's query to determine their intent. It uses an LLM
    to classify the query into one of four categories:
    - "cbt_protocol": User wants to create/design a CBT exercise
    - "question": User is asking a question about CBT/mental health
    - "conversation": User wants to have a conversation
    - "unknown": Cannot determine clear intent
    
    The function also extracts the LLM's reasoning/thinking about the classification,
    which can be streamed to the frontend for transparency.
    
    Args:
        user_query: The user's input query/request
        
    Returns:
        A tuple containing:
        - intent_type: One of "cbt_protocol", "question", "conversation", or "unknown"
        - thinking_reasoning: The LLM's reasoning about the classification
        
    Note:
        If the query is classified as "cbt_protocol", the workflow continues with
        the full multi-agent system. If "question" or "conversation", it's handled
        directly with a simple LLM response (bypassing the workflow).
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    system_prompt = """You are an intent classifier for a CBT exercise design system.

Analyze the user's query and determine their intent:

1. **cbt_protocol**: User wants to create, design, or generate a CBT exercise, protocol, or therapeutic intervention
   - Examples: "Create an exposure hierarchy", "Design a CBT exercise for anxiety", "I need a protocol for..."
   
2. **question**: User is asking a general question about CBT, mental health, therapy, or related topics
   - Examples: "What is CBT?", "How does exposure therapy work?", "Explain cognitive restructuring"
   
3. **conversation**: User wants to have a conversation, chat, or get general help
   - Examples: "Hi", "How are you?", "Can you help me?", "I'm feeling stressed"
   
4. **unknown**: Cannot determine clear intent

IMPORTANT: 
- If the query mentions creating, designing, or generating a CBT exercise/protocol → cbt_protocol
- If the query is asking for information or explanation → question
- If the query is conversational or seeking help → conversation
- Be flexible and consider context

Respond in this exact format:
THINKING: [Your reasoning about what the user wants]
INTENT: [cbt_protocol|question|conversation|unknown]
"""
    
    prompt = f"""User query: "{user_query}"

Classify the intent and explain your reasoning."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = await llm.ainvoke(messages)
    content = response.content.strip()
    
    # Parse response
    thinking = ""
    intent = "unknown"
    
    if "THINKING:" in content:
        thinking = content.split("THINKING:")[1].split("INTENT:")[0].strip()
    
    if "INTENT:" in content:
        intent_line = content.split("INTENT:")[1].strip().split("\n")[0].strip().lower()
        if intent_line in ["cbt_protocol", "question", "conversation", "unknown"]:
            intent = intent_line
    
    return intent, thinking




