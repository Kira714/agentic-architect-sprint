"""
LangGraph workflow definition
Implements the Supervisor-Worker pattern with autonomous agents.
"""
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from state import FoundryState
from agents.supervisor import create_supervisor_agent
from agents.draftsman import create_draftsman_agent
from agents.safety_guardian import create_safety_guardian_agent
from agents.clinical_critic import create_clinical_critic_agent
from agents.debate_moderator import create_debate_moderator_agent
from database import get_checkpointer
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


async def create_foundry_graph():
    """Create and configure the LangGraph workflow"""
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7
    )
    
    # Create agents
    supervisor = create_supervisor_agent(llm)
    draftsman = create_draftsman_agent(llm)
    safety_guardian = create_safety_guardian_agent(llm)
    clinical_critic = create_clinical_critic_agent(llm)
    debate_moderator = create_debate_moderator_agent(llm)
    
    # Create graph
    workflow = StateGraph(FoundryState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("draftsman", draftsman)
    workflow.add_node("safety_guardian", safety_guardian)
    workflow.add_node("clinical_critic", clinical_critic)
    workflow.add_node("debate_moderator", debate_moderator)
    
    # Add halt node (for human-in-the-loop)
    async def halt_node(state: FoundryState) -> FoundryState:
        """
        Halt execution and wait for human approval.
        State is checkpointed to database - can be resumed later.
        """
        print("[HALT] Execution halted for human review - state checkpointed to database")
        return {
            **state,
            "is_halted": True,
            "awaiting_human_approval": True,
            "current_agent": None,
            "last_updated": datetime.now().isoformat()
        }
    
    # Add approve node (finalize)
    async def approve_node(state: FoundryState) -> FoundryState:
        """Finalize the protocol"""
        print("[APPROVE] Finalizing protocol")
        final_draft = state.get('human_edited_draft') or state.get('current_draft', '')
        return {
            **state,
            "is_approved": True,
            "final_protocol": final_draft,
            "is_halted": False,
            "awaiting_human_approval": False,
            "last_updated": datetime.now().isoformat()
        }
    
    workflow.add_node("halt", halt_node)
    workflow.add_node("approve", approve_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor
    def route_decision(state: FoundryState) -> str:
        """Route based on supervisor's decision"""
        # Get the decision from the state (set by supervisor)
        decision = state.get('next_action', 'draftsman')
        # Clear it for next iteration
        if 'next_action' in state:
            state['next_action'] = None
        return decision
    
    workflow.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "draftsman": "draftsman",
            "safety_guardian": "safety_guardian",
            "clinical_critic": "clinical_critic",
            "debate_moderator": "debate_moderator",
            "halt": "halt",
            "approve": "approve"
        }
    )
    
    # All worker agents return to supervisor
    workflow.add_edge("draftsman", "supervisor")
    workflow.add_edge("safety_guardian", "supervisor")
    workflow.add_edge("clinical_critic", "supervisor")
    workflow.add_edge("debate_moderator", "supervisor")
    
    # Halt and approve are terminal
    workflow.add_edge("halt", END)
    workflow.add_edge("approve", END)
    
    # Get checkpointer
    checkpointer = await get_checkpointer()
    
    # Compile graph with checkpointer
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


async def run_foundry_workflow(
    user_query: str,
    user_intent: str,
    thread_id: str,
    max_iterations: int = 10
) -> FoundryState:
    """
    Run the foundry workflow for a user query.
    
    Args:
        user_query: The user's request
        user_intent: Extracted intent
        thread_id: Unique thread identifier for checkpointing
        max_iterations: Maximum iterations before halting
    
    Returns:
        Final state
    """
    graph = await create_foundry_graph()
    
    # Initial state
    initial_state: FoundryState = {
        "user_intent": user_intent,
        "user_query": user_query,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "is_approved": False,
        "is_halted": False,
        "current_agent": None,
        "current_draft": None,
        "draft_versions": [],
        "current_version": 0,
        "draft_edits": [],
        "agent_notes": [],
        "user_specifics": {},
        "agent_debate": [],
        "debate_complete": False,
        "learned_patterns": [],
        "adaptation_notes": [],
        "safety_review": None,
        "clinical_review": None,
        "started_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "final_protocol": None,
        "human_feedback": None,
        "human_edited_draft": None,
        "awaiting_human_approval": False
    }
    
    # Run the graph
    config = {"configurable": {"thread_id": thread_id}}
    
    # Stream execution
    final_state = None
    async for event in graph.astream(initial_state, config):
        # Yield events for real-time updates
        for node_name, node_state in event.items():
            final_state = node_state
            yield event
    
    # Return final state (if needed, can be accessed from last yielded event)
    # Note: This is an async generator, so we can't return a value
    # The caller should use the last yielded event

