"""
MAIN MCP Server for Personal MCP Chatbot
===========================================

This is the PRIMARY and PRODUCTION-READY MCP (Model Context Protocol) server implementation.

PURPOSE:
--------
Exposes the LangGraph multi-agent workflow as an MCP tool for machine-to-machine communication.
This allows AI assistants (like Claude Desktop) to create CBT protocols programmatically
without using the React UI.

KEY FEATURES:
-------------
1. **Comprehensive Logging**: File-based and stderr logging for debugging
2. **Intent Classification**: Routes questions vs CBT protocol requests (same as web version)
3. **Auto-Approval**: Automatically approves halted workflows (no human-in-the-loop for MCP)
4. **Error Handling**: Robust error handling with checkpoint recovery
5. **State Management**: Handles user questions, auto-proceeds without user input
6. **Checkpoint Integration**: Retrieves final state from checkpoint for consistency

HOW IT WORKS:
-------------
1. MCP client (e.g., Claude Desktop) calls the `create_cbt_protocol` tool
2. Server classifies intent (cbt_protocol, question, or conversation)
3. If question: Returns direct LLM response (bypasses workflow)
4. If cbt_protocol: Executes full multi-agent workflow:
   - Creates LangGraph workflow
   - Streams through all agent nodes
   - Auto-approves if workflow halts (MCP has no human-in-the-loop)
   - Retrieves final state from checkpoint
   - Returns protocol directly to MCP client

DIFFERENCES FROM WEB VERSION:
-----------------------------
- No human-in-the-loop: Auto-approves halted workflows
- No SSE streaming: Returns complete result at once
- Direct return: Protocol returned directly to MCP client
- Auto-handles questions: Marks information_gathered=True to skip user questions

USAGE:
------
Configured in Claude Desktop config file pointing to this script.
The server runs via stdio (standard input/output) for MCP communication.

NOTE:
-----
This is the MAIN MCP server. The file in mcp_server/mcp_server.py is a simpler
reference implementation. Use THIS file for production MCP integration.
"""
import sys
import traceback
import logging
from pathlib import Path

# Set up file-based logging as backup (since stderr may not be captured via SSH)
# Use temp directory that works on both Windows and Unix
import tempfile
log_file = Path(tempfile.gettempdir()) / "mcp_server.log"
try:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)
        ]
    )
except Exception as log_error:
    # If file logging fails, just use stderr
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
logger = logging.getLogger(__name__)

# Add error logging to stderr so it appears in Claude Desktop logs
def log_error(msg):
    print(f"[MCP ERROR] {msg}", file=sys.stderr, flush=True)
    logger.error(msg)

def log_info(msg):
    print(f"[MCP INFO] {msg}", file=sys.stderr, flush=True)
    logger.info(msg)

try:
    log_info("Starting MCP server import...")
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    log_info("MCP imports successful")
except Exception as e:
    log_error(f"Failed to import MCP: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    log_info("Importing project modules...")
    import asyncio
    from graph import create_foundry_graph
    from database import get_checkpointer
    from state import FoundryState
    from intent_classifier import classify_intent
    from datetime import datetime
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    import uuid
    import json
    import os
    from dotenv import load_dotenv
    log_info("Project imports successful")
except Exception as e:
    log_error(f"Failed to import project modules: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

try:
    log_info("Loading environment variables...")
    load_dotenv()
    
    # Ensure we're in the backend directory for relative paths (like SQLite DB)
    backend_dir = Path(__file__).parent
    if backend_dir.exists() and (backend_dir / "main.py").exists():
        os.chdir(backend_dir)
        log_info(f"Changed working directory to: {backend_dir}")
    
    log_info(f"Environment loaded, DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:60]}...")
    log_info(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
except Exception as e:
    log_error(f"Failed to load environment: {e}")
    traceback.print_exc(file=sys.stderr)

# Create MCP server
try:
    log_info("Creating MCP server instance...")
    app = Server("personal-mcp-chatbot")
    log_info("MCP server instance created")
except Exception as e:
    log_error(f"Failed to create MCP server: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available MCP tools.
    
    This function is called by the MCP client to discover available tools.
    It returns the list of tools this server exposes. Currently exposes
    one tool: `create_cbt_protocol`.
    
    Returns:
        List of Tool objects that can be called by MCP clients
        
    Note:
        This is part of the MCP protocol - clients call this to see what
        tools are available before calling them.
    """
    return [
        Tool(
            name="create_protocol",
            description="Create a personalized protocol or response using the multi-agent system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's request for the chatbot"
                    },
                    "user_specifics": {
                        "type": "object",
                        "description": "Optional user-specific information for personalization",
                        "additionalProperties": True
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum iterations before halting (default: 10)",
                        "default": 10
                    }
                },
                "required": ["user_query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.
    
    This is the MAIN MCP SERVER LOGIC - the core function that executes when
    an MCP client (e.g., Claude Desktop) calls the create_cbt_protocol tool.
    
    WORKFLOW EXECUTION FLOW:
    ------------------------
    1. Receives tool call with user_query and optional parameters
    2. Classifies intent (cbt_protocol, question, or conversation)
    3. If question: Returns direct LLM chat response (bypasses workflow)
    4. If cbt_protocol: Executes full multi-agent workflow:
       a. Creates LangGraph workflow graph
       b. Initializes state with user query and specifics
       c. Streams workflow execution (all agents run autonomously)
       d. Auto-handles user questions (marks information_gathered=True)
       e. Auto-approves if workflow halts (MCP has no human-in-the-loop)
       f. Retrieves final state from checkpoint
       g. Extracts final protocol
    5. Returns complete result as JSON to MCP client
    
    KEY DIFFERENCES FROM WEB VERSION:
    ----------------------------------
    - Auto-approval: If workflow halts, automatically approves and continues
    - No user questions: Auto-marks information_gathered=True to skip questions
    - Direct return: Returns complete result at once (no SSE streaming)
    - Checkpoint recovery: Always retrieves final state from checkpoint
    
    Args:
        name: Tool name (should be "create_cbt_protocol")
        arguments: Dictionary containing:
            - user_query (required): User's request for CBT exercise
            - user_specifics (optional): User-specific information
            - max_iterations (optional, default: 10): Max iterations before halting
            
    Returns:
        List of TextContent objects containing the result as JSON
        
    Note:
        This function handles all errors gracefully and returns error responses
        instead of raising exceptions, as required by MCP protocol.
    """
    log_info("=" * 80)
    log_info(f"[MCP TOOL CALL] name={name}, arguments_keys={list(arguments.keys())}")
    
    if name == "create_protocol":
        user_query = arguments.get("user_query", "")
        user_specifics = arguments.get("user_specifics", {})
        max_iterations = arguments.get("max_iterations", 10)
        
        log_info(f"[MCP] user_query length: {len(user_query)}, user_specifics: {bool(user_specifics)}, max_iterations: {max_iterations}")
        
        if not user_query:
            log_error("[MCP] Missing user_query")
            return [TextContent(
                type="text",
                text="Error: user_query is required"
            )]
        
        try:
            log_info("[MCP] Starting protocol creation workflow...")
            # Create thread ID
            thread_id = str(uuid.uuid4())
            log_info(f"[MCP] Generated thread_id: {thread_id}")
            log_info(f"[MCP] Starting workflow for query: {user_query[:50]}...")
            
            # Classify intent (same as web version)
            log_info("[MCP] Step 1: Classifying user intent...")
            try:
                intent, thinking = await classify_intent(user_query)
                log_info(f"[MCP] ✅ Intent classified: {intent}, thinking length: {len(thinking)}")
                user_intent = intent
                
                # Handle non-CBT protocol requests (questions) - same as web version
                if intent == "question":
                    log_info("[MCP] Intent is 'question', handling as chat request")
                    llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.7,
                        api_key=os.getenv("OPENAI_API_KEY")
                    )
                    
                    system_prompt = """You are a helpful assistant knowledgeable about Cognitive Behavioral Therapy (CBT), mental health, and therapeutic techniques.

Provide clear, accurate, and empathetic answers to questions about:
- CBT techniques and principles
- Mental health topics
- Therapeutic approaches
- Self-help strategies
- Psychology concepts

Be conversational, warm, and supportive. Use examples when helpful."""
                    
                    response = await llm.ainvoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_query)
                    ])
                    
                    # Return question response directly
                    response_text = response.content
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "thread_id": thread_id,
                            "status": "completed",
                            "protocol": None,
                            "response": response_text,
                            "intent": "question",
                            "metadata": {
                                "iterations": 0,
                                "type": "chat_response"
                            }
                        }, indent=2, ensure_ascii=False)
                    )]
            except Exception as intent_error:
                log_error(f"Error classifying intent: {intent_error}")
                traceback.print_exc(file=sys.stderr)
                # Fallback: use user_query as intent
                user_intent = user_query
            
            # Create graph
            log_info("[MCP] Step 2: Creating workflow graph...")
            try:
                graph = await create_foundry_graph()
                log_info("[MCP] ✅ Graph created successfully")
            except Exception as graph_error:
                log_error(f"[MCP] ❌ Failed to create graph: {graph_error}")
                traceback.print_exc(file=sys.stderr)
                raise
            
            config = {"configurable": {"thread_id": thread_id}}
            log_info(f"[MCP] Config: {config}")
            log_info(f"[MCP] DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:60]}...")
            log_info(f"[MCP] OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
            
            # Initial state (same structure as web version)
            # For MCP: Always mark information as gathered to skip questions and proceed directly
            initial_state: FoundryState = {
                "user_intent": user_intent,
                "user_query": user_query,
                "user_specifics": user_specifics,
                "information_gathered": True,  # MCP: Skip questions, proceed directly
                "questions_for_user": None,
                "awaiting_user_response": False,
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
                "awaiting_human_approval": False,
                "next_action": None
            }
            
            # Run workflow (same pattern as web version)
            log_info("[MCP] Step 3: Preparing to execute workflow...")
            final_state = None
            
            try:
                # Stream through all events (same as web version)
                event_count = 0
                last_state = initial_state
                log_info("[MCP] ==================== WORKFLOW EXECUTION START ====================")
                log_info(f"[MCP] Initial state keys ({len(initial_state)}): {list(initial_state.keys())[:15]}...")
                log_info(f"[MCP] user_intent: {initial_state.get('user_intent', 'N/A')[:50]}")
                log_info(f"[MCP] user_query: {initial_state.get('user_query', 'N/A')[:50]}")
                log_info(f"[MCP] information_gathered: {initial_state.get('information_gathered', False)}")
                log_info(f"[MCP] Config: {config}")
                
                # Try astream first
                stream_started = False
                try:
                    log_info("[MCP] ========== CALLING graph.astream() ==========")
                    stream = graph.astream(initial_state, config)
                    log_info("[MCP] astream() returned generator, starting iteration...")
                    
                    async for event in stream:
                        stream_started = True
                        event_count += 1
                        log_info(f"[MCP] ════════════════════════════════════════════════════════════")
                        log_info(f"[MCP] 📨 EVENT #{event_count} RECEIVED")
                        log_info(f"[MCP] Event keys: {list(event.keys())}")
                        
                        # Process each node in the event (same as web version)
                        for node_name, node_state in event.items():
                            last_state = node_state
                            iterations = node_state.get('iteration_count', 0)
                            has_draft = bool(node_state.get('current_draft'))
                            draft_len = len(node_state.get('current_draft', '')) if node_state.get('current_draft') else 0
                            log_info(f"[MCP] 📍 NODE: {node_name}")
                            log_info(f"[MCP]    └─ Iterations: {iterations}")
                            log_info(f"[MCP]    └─ Has draft: {has_draft} (length: {draft_len})")
                            log_info(f"[MCP]    └─ Is halted: {node_state.get('is_halted', False)}")
                            log_info(f"[MCP]    └─ Is approved: {node_state.get('is_approved', False)}")
                            log_info(f"[MCP]    └─ Current agent: {node_state.get('current_agent')}")
                        
                        # Auto-handle user questions for MCP (no human in the loop)
                        if node_state.get("awaiting_user_response") or node_state.get("questions_for_user"):
                            log_info(f"[MCP] 🔄 Auto-handling user questions (MCP mode - no human in loop)")
                            questions = node_state.get("questions_for_user")
                            if questions:
                                log_info(f"[MCP] Questions detected: {len(questions) if isinstance(questions, list) else 'unknown'}")
                                log_info(f"[MCP] Auto-marking as information_gathered=True to proceed without user input")
                            # Auto-proceed without user answers for MCP - mark as gathered and continue
                            updated_state = {
                                **node_state,
                                "is_halted": False,
                                "awaiting_user_response": False,
                                "questions_for_user": None,  # Clear questions
                                "information_gathered": True,  # Mark as gathered to proceed
                                "last_updated": datetime.now().isoformat()
                            }
                            await graph.aupdate_state(config, updated_state)
                            log_info(f"[MCP] State updated to continue workflow without user input")
                            # Continue workflow instead of breaking - let it proceed to draftsman
                            continue
                        
                        # Check if halted (for human approval) - same as web version
                        if node_state.get("is_halted") or node_state.get("awaiting_human_approval"):
                            log_info(f"[MCP] ⏸️ Halted detected: is_halted={node_state.get('is_halted')}, awaiting_approval={node_state.get('awaiting_human_approval')}")
                            
                            # Auto-approve for MCP (no human in the loop)
                            current_draft = node_state.get("current_draft")
                            if current_draft:
                                log_info(f"[MCP] ✅ Auto-approving draft (length: {len(current_draft)})")
                                updated_state = {
                                    **node_state,
                                    "is_halted": False,
                                    "awaiting_human_approval": False,
                                    "is_approved": True,
                                    "final_protocol": current_draft,
                                    "last_updated": datetime.now().isoformat()
                                }
                                await graph.aupdate_state(config, updated_state)
                                final_state = updated_state
                                break
                            else:
                                log_info("[MCP] ⚠️ Halted but no draft available yet, continuing workflow...")
                                # Don't break, let it continue
                                continue
                        
                        # Check if approved (same as web version)
                        if node_state.get("is_approved"):
                            log_info("Protocol approved")
                            final_state = node_state
                            break
                
                except Exception as stream_error:
                    log_error(f"[MCP] ❌❌❌ ERROR during astream: {stream_error}")
                    log_error(f"[MCP] Error type: {type(stream_error).__name__}")
                    import traceback as tb
                    tb.print_exc(file=sys.stderr)
                    stream_started = True  # Mark that we tried
                    # Fall through to try ainvoke
                
                log_info(f"[MCP] ==================== STREAM COMPLETED ====================")
                log_info(f"[MCP] Summary: event_count={event_count}, stream_started={stream_started}")
                log_info(f"[MCP] last_state iterations: {last_state.get('iteration_count', 0) if isinstance(last_state, dict) else 'N/A'}")
                
                # If astream produced no events, try ainvoke directly
                if event_count == 0:
                    log_info("⚠️ astream produced no events, trying ainvoke instead...")
                    try:
                        log_info("Calling graph.ainvoke()...")
                        final_state = await graph.ainvoke(initial_state, config)
                        log_info(f"ainvoke returned: type={type(final_state)}, iterations={final_state.get('iteration_count', 0) if final_state and isinstance(final_state, dict) else 'N/A'}")
                        log_info(f"ainvoke state keys: {list(final_state.keys()) if final_state and isinstance(final_state, dict) else 'None'}")
                        if final_state:
                            if isinstance(final_state, dict):
                                last_state = final_state
                                log_info(f"Using ainvoke result: iterations={last_state.get('iteration_count', 0)}")
                            else:
                                log_error(f"ainvoke returned unexpected type: {type(final_state)}")
                    except Exception as ainvoke_error:
                        log_error(f"❌ ainvoke also failed: {ainvoke_error}")
                        import traceback as tb
                        tb.print_exc(file=sys.stderr)
                        # Try to get error details
                        import sys
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        log_error(f"Exception type: {exc_type}, value: {exc_value}")
                        # Don't raise, let the error handling below deal with it
                
                # If we didn't halt or complete, check final state (same as web version)
                if not final_state:
                    if last_state and not (last_state.get("is_halted") or last_state.get("is_approved")):
                        # Check if we hit max iterations
                        if last_state.get("iteration_count", 0) >= last_state.get("max_iterations", 10):
                            log_info("Max iterations reached")
                            # Use last state
                            final_state = last_state
                        else:
                            # Try to get final state using ainvoke (same as web version fallback)
                            log_info("Stream ended without completion, using ainvoke to get final state...")
                            try:
                                final_state = await graph.ainvoke(initial_state, config)
                                log_info(f"Got final state via ainvoke: iterations={final_state.get('iteration_count', 0)}")
                            except Exception as ainvoke_error:
                                log_error(f"Error with ainvoke: {ainvoke_error}")
                                # Fall back to last state
                                final_state = last_state
                    else:
                        final_state = last_state
                
                # Always get final state from checkpoint (same as web version)
                if final_state:
                    log_info("Getting final state from checkpoint to ensure consistency...")
                    try:
                        checkpoint_state = await graph.aget_state(config)
                        if checkpoint_state and checkpoint_state.values:
                            final_state = checkpoint_state.values
                            log_info(f"Final state from checkpoint: iterations={final_state.get('iteration_count', 0)}, draft_exists={bool(final_state.get('current_draft'))}")
                    except Exception as checkpoint_error:
                        log_error(f"Error getting checkpoint state: {checkpoint_error}")
                        # Use the final_state we already have
                    
            except Exception as workflow_error:
                log_error(f"Workflow execution error: {workflow_error}")
                import traceback as tb
                tb.print_exc(file=sys.stderr)
                # Try to get state from checkpoint even on error
                try:
                    checkpoint_state = await graph.aget_state(config)
                    if checkpoint_state and checkpoint_state.values:
                        final_state = checkpoint_state.values
                        log_info(f"Recovered state from checkpoint after error: iterations={final_state.get('iteration_count', 0)}")
                except Exception as checkpoint_recovery_error:
                    log_error(f"Failed to recover from checkpoint: {checkpoint_recovery_error}")
                
                # If we still don't have a state, create an error response instead of raising
                if not final_state:
                    error_response = {
                        "thread_id": thread_id,
                        "status": "error",
                        "protocol": None,
                        "error": str(workflow_error),
                        "metadata": {
                            "iterations": 0,
                            "error_type": type(workflow_error).__name__
                        }
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(error_response, indent=2, ensure_ascii=False)
                    )]
            
            # Extract final protocol (same logic as web version)
            log_info("[MCP] ==================== EXTRACTING PROTOCOL ====================")
            if not final_state:
                log_error("[MCP] ❌ final_state is None!")
            elif not isinstance(final_state, dict):
                log_error(f"[MCP] ❌ final_state is not a dict, it's {type(final_state)}")
            else:
                log_info(f"[MCP] final_state type: {type(final_state)}, keys: {list(final_state.keys())[:15]}...")
            
            final_protocol = final_state.get("final_protocol") or final_state.get("current_draft", "") if final_state and isinstance(final_state, dict) else ""
            final_protocol = final_protocol if final_protocol else ""  # Ensure it's never None
            
            log_info(f"[MCP] Protocol extraction:")
            log_info(f"[MCP]    └─ final_protocol exists: {bool(final_state.get('final_protocol') if final_state and isinstance(final_state, dict) else False)}")
            log_info(f"[MCP]    └─ current_draft exists: {bool(final_state.get('current_draft') if final_state and isinstance(final_state, dict) else False)}")
            log_info(f"[MCP]    └─ extracted protocol length: {len(final_protocol) if final_protocol else 0}")
            
            # Ensure protocol is a string and handle None/empty cases
            if not final_protocol:
                log_info("Warning: No protocol generated in final state")
                # Check if there's any draft version history
                draft_versions = final_state.get("draft_versions", [])
                if draft_versions:
                    log_info(f"Checking draft_versions history: {len(draft_versions)} versions found")
                    # Get the latest draft version
                    latest_version = draft_versions[-1] if draft_versions else None
                    if latest_version and isinstance(latest_version, dict):
                        final_protocol = latest_version.get("content", "") or ""
                        log_info(f"Using latest draft version (length: {len(final_protocol) if final_protocol else 0})")
            
            # Format response with proper error handling for encoding
            log_info("[MCP] ==================== FORMATTING RESPONSE ====================")
            try:
                # Debug: Log what we have
                log_info(f"[MCP] Preparing response:")
                log_info(f"[MCP]    └─ final_state type: {type(final_state)}")
                if final_state and isinstance(final_state, dict):
                    log_info(f"[MCP]    └─ final_state keys ({len(final_state)}): {list(final_state.keys())[:15]}...")
                    log_info(f"[MCP]    └─ iteration_count: {final_state.get('iteration_count', 'NOT_FOUND')}")
                    log_info(f"[MCP]    └─ current_draft exists: {bool(final_state.get('current_draft'))}")
                    log_info(f"[MCP]    └─ final_protocol exists: {bool(final_state.get('final_protocol'))}")
                    log_info(f"[MCP]    └─ agent_notes count: {len(final_state.get('agent_notes', []))}")
                else:
                    log_error(f"[MCP] ❌ final_state is invalid: {final_state}")
                
                response = {
                    "thread_id": thread_id,
                    "status": "completed",
                    "protocol": final_protocol if final_protocol else None,
                    "metadata": {
                        "iterations": final_state.get("iteration_count", 0) if final_state and isinstance(final_state, dict) else 0,
                        "safety_review": final_state.get("safety_review", {}).get("status") if final_state and isinstance(final_state, dict) and final_state.get("safety_review") else None,
                        "clinical_review": final_state.get("clinical_review", {}).get("status") if final_state and isinstance(final_state, dict) and final_state.get("clinical_review") else None,
                        "has_draft": bool(final_protocol),
                        "current_agent": str(final_state.get("current_agent")) if final_state and isinstance(final_state, dict) else None,
                        "debug_info": {
                            "event_count": event_count,
                            "final_state_type": str(type(final_state)),
                            "final_state_keys": list(final_state.keys())[:10] if final_state and isinstance(final_state, dict) else []
                        }
                    }
                }
                
                # Serialize with ensure_ascii=False to handle unicode characters properly
                response_text = json.dumps(response, indent=2, ensure_ascii=False)
                log_info(f"[MCP] ✅ Response formatted successfully")
                log_info(f"[MCP]    └─ Protocol length: {len(final_protocol) if final_protocol else 0}")
                log_info(f"[MCP]    └─ Response JSON length: {len(response_text)}")
                log_info("[MCP] ==================== WORKFLOW COMPLETE ====================")
                log_info("=" * 80)
                
                return [TextContent(
                    type="text",
                    text=response_text
                )]
            except (UnicodeEncodeError, UnicodeDecodeError) as encoding_error:
                log_error(f"Encoding error when serializing response: {encoding_error}")
                # Fallback: encode as UTF-8 and replace errors
                if final_protocol:
                    final_protocol_encoded = final_protocol.encode('utf-8', errors='replace').decode('utf-8')
                else:
                    final_protocol_encoded = None
                response = {
                    "thread_id": thread_id,
                    "status": "completed",
                    "protocol": final_protocol_encoded,
                    "metadata": {
                        "iterations": final_state.get("iteration_count", 0),
                        "error": "Encoding issue resolved",
                        "has_draft": bool(final_protocol_encoded)
                    }
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(response, indent=2, ensure_ascii=False)
                )]
            
        except Exception as e:
            import traceback as tb
            error_msg = f"Error creating CBT protocol: {str(e)}\n{tb.format_exc()}"
            return [TextContent(
                type="text",
                text=error_msg
            )]
    
    return [TextContent(
        type="text",
        text=f"Unknown tool: {name}"
    )]


async def main():
    """
    Main entry point for MCP server.
    
    This function starts the MCP server using stdio (standard input/output)
    communication. The server listens for MCP protocol messages on stdin
    and responds on stdout. This is the standard MCP communication method.
    
    The server runs indefinitely until interrupted or an error occurs.
    All communication follows the MCP (Model Context Protocol) standard.
    
    Note:
        This is called when the script is executed directly. The server
        communicates via stdio, which is how MCP clients (like Claude Desktop)
        interact with MCP servers.
    """
    try:
        log_info("Starting stdio server...")
        # Force flush stderr to ensure logs are visible
        sys.stderr.flush()
        
        async with stdio_server() as (read_stream, write_stream):
            log_info("Stdio server started, running app...")
            sys.stderr.flush()
            
            # Get initialization options
            init_options = app.create_initialization_options()
            log_info(f"Initialization options: {init_options}")
            sys.stderr.flush()
            
            # Run the app
            try:
                await app.run(
                    read_stream,
                    write_stream,
                    init_options
                )
            except Exception as run_error:
                log_error(f"Error in app.run: {run_error}")
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                raise
    except Exception as e:
        log_error(f"MCP server error: {e}")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


if __name__ == "__main__":
    try:
        log_info("MCP server starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("MCP server interrupted")
    except Exception as e:
        log_error(f"Fatal error: {e}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

