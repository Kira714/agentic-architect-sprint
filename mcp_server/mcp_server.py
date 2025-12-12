"""
MCP Server for Cerina Protocol Foundry
Exposes the LangGraph workflow as an MCP tool.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from graph import create_foundry_graph
from state import FoundryState
from datetime import datetime
import uuid

# Initialize MCP server
server = Server("cerina-foundry")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="create_cbt_protocol",
            description="Create a CBT (Cognitive Behavioral Therapy) exercise protocol. "
                        "This tool uses an autonomous multi-agent system to design, critique, "
                        "and refine CBT exercises based on user intent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's request for a CBT exercise (e.g., 'Create an exposure hierarchy for agoraphobia')"
                    },
                    "user_intent": {
                        "type": "string",
                        "description": "Optional: Extracted intent from the user query",
                        "default": None
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum number of iterations before halting (default: 10)",
                        "default": 10
                    }
                },
                "required": ["user_query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "create_cbt_protocol":
        user_query = arguments.get("user_query", "")
        user_intent = arguments.get("user_intent") or user_query
        max_iterations = arguments.get("max_iterations", 10)
        
        if not user_query:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "user_query is required"
                    }, indent=2)
                )
            ]
        
        try:
            # Create graph
            graph = await create_foundry_graph()
            
            # Generate unique thread ID
            thread_id = str(uuid.uuid4())
            
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
                "agent_notes": [],
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
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Run the workflow
            # For MCP, we'll run it to completion (no human-in-the-loop interruption)
            # In a real scenario, you might want to handle halting differently
            
            final_state = None
            async for event in graph.astream(initial_state, config):
                # Process events
                for node_name, node_state in event.items():
                    final_state = node_state
                    
                    # Auto-approve if halted (for MCP use case)
                    if node_state.get("is_halted") or node_state.get("awaiting_human_approval"):
                        # Auto-approve and continue
                        updated_state = {
                            **node_state,
                            "is_halted": False,
                            "awaiting_human_approval": False,
                            "is_approved": True,
                            "human_edited_draft": node_state.get("current_draft"),
                        }
                        # Continue to approval
                        final_state = await graph.ainvoke(updated_state, config)
                        break
            
            # If we didn't get a final state, invoke once more
            if not final_state or not final_state.get("final_protocol"):
                final_state = await graph.ainvoke(initial_state, config)
            
            # Format response
            result = {
                "thread_id": thread_id,
                "status": "completed",
                "protocol": final_state.get("final_protocol") or final_state.get("current_draft", ""),
                "metadata": {
                    "iterations": final_state.get("iteration_count", 0),
                    "versions": final_state.get("current_version", 0),
                    "safety_status": final_state.get("safety_review", {}).get("status") if final_state.get("safety_review") else None,
                    "clinical_status": final_state.get("clinical_review", {}).get("status") if final_state.get("clinical_review") else None,
                    "agent_notes_count": len(final_state.get("agent_notes", [])),
                }
            }
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "type": type(e).__name__
                    }, indent=2)
                )
            ]
    
    else:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}"
                }, indent=2)
            )
        ]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())





