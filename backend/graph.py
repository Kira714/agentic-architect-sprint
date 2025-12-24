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
    """
    Create and configure the LangGraph workflow graph.
    
    This function builds the complete workflow graph using the Supervisor-Worker pattern.
    It creates all agent nodes, defines the graph structure with edges, sets up routing
    logic, and attaches the checkpointer for state persistence.
    
    Graph Structure:
    - Entry Point: supervisor
    - Nodes: supervisor, draftsman, safety_guardian, clinical_critic, debate_moderator, halt, approve
    - Conditional Edges: From supervisor to workers based on routing decision
    - Edges: All workers return to supervisor; halt and approve are terminal (END)
    
    The checkpointer is attached at graph compilation, which enables automatic checkpointing
    after every node execution. This allows the workflow to resume from any point if interrupted.
    
    Returns:
        A compiled LangGraph application that can be executed with astream() or ainvoke()
        
    Note:
        This function is async because it needs to await get_checkpointer() which may
        perform database setup operations.
    """
    
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
        Halt node function - stops workflow execution for human review.
        
        This function is called when the Supervisor routes to "halt". It marks the
        workflow as halted and awaiting human approval. The state is automatically
        checkpointed by LangGraph, allowing the workflow to be resumed later after
        human review and approval.
        
        This is a terminal node - the workflow ends here (routes to END) until
        human approval is received via the /api/protocols/{thread_id}/approve endpoint.
        
        Args:
            state: The current FoundryState
            
        Returns:
            Updated FoundryState with:
            - is_halted: Set to True
            - awaiting_human_approval: Set to True
            - current_agent: Set to None
            - last_updated: Timestamp
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
        """
        Approve node function - finalizes the protocol.
        
        This function is called when the Supervisor routes to "approve" (typically after
        human approval). It marks the workflow as approved and sets the final_protocol.
        The final protocol is taken from human_edited_draft (if human made edits) or
        current_draft (if no edits).
        
        This is a terminal node - the workflow ends here (routes to END) and is complete.
        
        Args:
            state: The current FoundryState
            
        Returns:
            Updated FoundryState with:
            - is_approved: Set to True
            - final_protocol: Set to human_edited_draft or current_draft
            - is_halted: Set to False
            - awaiting_human_approval: Set to False
            - last_updated: Timestamp
        """
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
        """
        Routing function - determines next node based on Supervisor's decision.
        
        This function is used by LangGraph's conditional edges to determine which node
        to execute after the Supervisor completes. It reads the next_action field from
        the state (set by the Supervisor) and returns it as the routing decision.
        
        The next_action is cleared after reading to prevent it from being reused in
        subsequent iterations.
        
        Args:
            state: The current FoundryState with next_action set by Supervisor
            
        Returns:
            String indicating which node to route to:
            - "draftsman": Route to Draftsman agent
            - "safety_guardian": Route to Safety Guardian agent
            - "clinical_critic": Route to Clinical Critic agent
            - "debate_moderator": Route to Debate Moderator agent
            - "halt": Route to halt node
            - "approve": Route to approve node
        """
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
    
    This function executes the complete workflow graph for a given user query.
    It creates the graph, initializes the state, and streams execution events.
    The workflow uses the thread_id for checkpointing, allowing it to resume
    from any point if interrupted.
    
    This is an async generator function - it yields events as the workflow executes,
    allowing real-time updates. The final state can be accessed from the last
    yielded event.
    
    Args:
        user_query: The user's original request/query
        user_intent: The classified intent (from intent classifier)
        thread_id: Unique identifier for this workflow execution (used for checkpointing)
        max_iterations: Maximum number of iterations before halting (default: 10)
    
    Yields:
        Events from graph.astream() - each event contains node name and node state
        
    Note:
        This is an async generator, so it doesn't return a value directly.
        The caller should iterate over the yielded events to get real-time updates
        and access the final state from the last event.
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

