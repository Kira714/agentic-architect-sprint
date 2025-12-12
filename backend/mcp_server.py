"""
MCP Server for Cerina Protocol Foundry
Exposes the LangGraph workflow as an MCP tool for machine-to-machine communication.
"""
import sys
import traceback
import logging
from pathlib import Path

# Set up file-based logging as backup (since stderr may not be captured via SSH)
log_file = Path("/tmp/mcp_server.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
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
    from datetime import datetime
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
    log_info("Environment loaded")
except Exception as e:
    log_error(f"Failed to load environment: {e}")
    traceback.print_exc(file=sys.stderr)

# Create MCP server
try:
    log_info("Creating MCP server instance...")
    app = Server("cerina-foundry")
    log_info("MCP server instance created")
except Exception as e:
    log_error(f"Failed to create MCP server: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="create_cbt_protocol",
            description="Create a CBT (Cognitive Behavioral Therapy) exercise protocol. This tool uses a multi-agent system with Supervisor, Draftsman, Safety Guardian, Clinical Critic, and Debate Moderator to create evidence-based, safe, and empathetic CBT exercises.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's request for a CBT exercise (e.g., 'Create an exposure hierarchy for agoraphobia')"
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
    """Handle tool calls"""
    if name == "create_cbt_protocol":
        user_query = arguments.get("user_query", "")
        user_specifics = arguments.get("user_specifics", {})
        max_iterations = arguments.get("max_iterations", 10)
        
        if not user_query:
            return [TextContent(
                type="text",
                text="Error: user_query is required"
            )]
        
        try:
            # Create thread ID
            thread_id = str(uuid.uuid4())
            
            # Create graph
            graph = await create_foundry_graph()
            config = {"configurable": {"thread_id": thread_id}}
            
            # Initial state
            initial_state: FoundryState = {
                "user_intent": user_query,
                "user_query": user_query,
                "user_specifics": user_specifics,
                "information_gathered": bool(user_specifics),
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
            
            # Run workflow (non-streaming for MCP)
            final_state = None
            async for event in graph.astream(initial_state, config):
                for node_name, node_state in event.items():
                    final_state = node_state
                    
                    # Check if halted (for human approval in MCP context, we auto-approve)
                    if node_state.get("is_halted") or node_state.get("awaiting_human_approval"):
                        # Auto-approve for MCP (no human in the loop)
                        if node_state.get("current_draft"):
                            updated_state = {
                                **node_state,
                                "is_halted": False,
                                "awaiting_human_approval": False,
                                "is_approved": True,
                                "final_protocol": node_state.get("current_draft"),
                                "last_updated": datetime.now().isoformat()
                            }
                            await graph.aupdate_state(config, updated_state)
                            final_state = updated_state
                            break
            
            # Get final state
            if not final_state:
                checkpoint_state = await graph.aget_state(config)
                final_state = checkpoint_state.values if checkpoint_state else initial_state
            
            # Extract final protocol
            final_protocol = final_state.get("final_protocol") or final_state.get("current_draft", "")
            
            # Format response
            response = {
                "thread_id": thread_id,
                "status": "completed",
                "protocol": final_protocol,
                "metadata": {
                    "iterations": final_state.get("iteration_count", 0),
                    "safety_review": final_state.get("safety_review", {}).get("status") if final_state.get("safety_review") else None,
                    "clinical_review": final_state.get("clinical_review", {}).get("status") if final_state.get("clinical_review") else None,
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
            
        except Exception as e:
            import traceback
            error_msg = f"Error creating CBT protocol: {str(e)}\n{traceback.format_exc()}"
            return [TextContent(
                type="text",
                text=error_msg
            )]
    
    return [TextContent(
        type="text",
        text=f"Unknown tool: {name}"
    )]


async def main():
    """Run MCP server"""
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

