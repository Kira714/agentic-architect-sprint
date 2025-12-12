"""
FastAPI server for Cerina Protocol Foundry
Provides REST API for React frontend and streaming support.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
import asyncio
from graph import create_foundry_graph, run_foundry_workflow
from database import get_checkpointer
from state import FoundryState
from datetime import datetime
from intent_classifier import classify_intent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

# Import history functions (may fail if table doesn't exist yet - that's OK)
try:
    from history import log_protocol_creation, update_protocol_status, get_protocol_history
    HISTORY_AVAILABLE = True
except ImportError as e:
    print(f"[MAIN] Warning: History module not available ({e}), skipping history logging")
    HISTORY_AVAILABLE = False
    async def log_protocol_creation(*args, **kwargs):
        pass
    async def update_protocol_status(*args, **kwargs):
        pass
    async def get_protocol_history(*args, **kwargs):
        return []

app = FastAPI(title="Cerina Protocol Foundry API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8010", "http://localhost:3000", "http://47.236.14.170:8010"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class CreateProtocolRequest(BaseModel):
    user_query: str
    user_intent: Optional[str] = None
    max_iterations: int = 10
    user_specifics: Optional[Dict[str, Any]] = None  # User responses to questions


class ProtocolResponse(BaseModel):
    thread_id: str
    status: str
    state: Optional[Dict[str, Any]] = None


class ApproveRequest(BaseModel):
    edited_draft: Optional[str] = None
    feedback: Optional[str] = None
    user_specifics: Optional[Dict[str, Any]] = None  # User responses to questions (if any)


# Store active workflows (in production, use Redis or database)
active_workflows: Dict[str, Any] = {}


@app.get("/")
async def root():
    return {"message": "Cerina Protocol Foundry API", "version": "1.0.0"}


@app.post("/api/protocols/create", response_model=ProtocolResponse)
async def create_protocol(request: CreateProtocolRequest):
    print(f"[API] POST /api/protocols/create - user_query: {request.user_query[:50]}...")
    """
    Create a new CBT protocol workflow.
    Returns immediately with thread_id for streaming.
    """
    thread_id = str(uuid.uuid4())
    user_intent = request.user_intent or request.user_query
    
    # Store workflow info
    active_workflows[thread_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "user_query": request.user_query,
        "user_specifics": request.user_specifics or {}  # Store user responses
    }
    
    # Log to history (if available)
    if HISTORY_AVAILABLE:
        try:
            await log_protocol_creation(
                thread_id=thread_id,
                user_query=request.user_query,
                user_intent=request.user_intent or request.user_query,
                user_specifics=request.user_specifics or {}
            )
        except Exception as e:
            print(f"[MAIN] Warning: Could not log protocol creation: {e}")
    
    return ProtocolResponse(
        thread_id=thread_id,
        status="created",
        state=None
    )


@app.get("/api/protocols/{thread_id}/stream")
async def stream_protocol(thread_id: str):
    """
    Stream protocol generation in real-time.
    Uses Server-Sent Events (SSE) for React frontend.
    """
    print(f"[STREAM] Starting stream for thread_id: {thread_id}")
    
    async def event_generator():
        try:
            print(f"[STREAM] Event generator started for thread: {thread_id}")
            
            # Get workflow info
            workflow_info = active_workflows.get(thread_id)
            if not workflow_info:
                error_msg = f"Workflow not found for thread_id: {thread_id}"
                print(f"[STREAM] ERROR: {error_msg}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": error_msg, "event": "error"})
                }
                return
            
            print(f"[STREAM] Found workflow: {workflow_info}")
            user_query = workflow_info["user_query"]
            
            # Classify intent and get thinking
            print(f"[STREAM] Classifying user intent...")
            try:
                intent, thinking = await classify_intent(user_query)
                print(f"[STREAM] Intent classified: {intent}")
                
                # Send thinking message (stream character by character for smooth effect)
                print(f"[STREAM] Streaming thinking, length: {len(thinking)}")
                for i in range(len(thinking)):
                    try:
                        yield {
                            "event": "thinking",
                            "data": json.dumps({
                                "event": "thinking",
                                "agent": "Intent Classifier",
                                "content": thinking[:i+1],
                                "intent": intent,
                                "timestamp": datetime.now().isoformat(),
                                "is_complete": i == len(thinking) - 1
                            })
                        }
                        if i % 10 == 0:  # Small delay every 10 characters
                            await asyncio.sleep(0.02)
                    except Exception as stream_err:
                        print(f"[STREAM] Error streaming thinking: {stream_err}")
                        import traceback
                        traceback.print_exc()
                        break
                print(f"[STREAM] Thinking streaming complete")
                
                # Handle non-CBT protocol requests
                if intent == "question":
                    print(f"[STREAM] Handling as question")
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
                    
                    # Stream response character by character
                    response_text = response.content
                    print(f"[STREAM] Streaming response (question), length: {len(response_text)}")
                    for i in range(len(response_text)):
                        try:
                            yield {
                                "event": "response",
                                "data": json.dumps({
                                    "event": "response",
                                    "content": response_text[:i+1],
                                    "timestamp": datetime.now().isoformat(),
                                    "is_complete": i == len(response_text) - 1
                                })
                            }
                            if i % 10 == 0:  # Small delay every 10 characters
                                await asyncio.sleep(0.02)
                        except Exception as stream_err:
                            print(f"[STREAM] Error streaming response: {stream_err}")
                            import traceback
                            traceback.print_exc()
                            break
                    
                    print(f"[STREAM] Response streaming complete (question)")
                    active_workflows[thread_id]["status"] = "completed"
                    return
                
                elif intent == "conversation":
                    print(f"[STREAM] Handling as conversation")
                    llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.7,
                        api_key=os.getenv("OPENAI_API_KEY")
                    )
                    
                    system_prompt = """You are a supportive, empathetic assistant. You help people with mental health questions and can create CBT exercises when needed.

Be warm, understanding, and helpful. If the user seems to need a CBT exercise, gently suggest creating one."""
                    
                    response = await llm.ainvoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_query)
                    ])
                    
                    # Stream response character by character
                    response_text = response.content
                    print(f"[STREAM] Streaming response (conversation), length: {len(response_text)}")
                    for i in range(len(response_text)):
                        try:
                            yield {
                                "event": "response",
                                "data": json.dumps({
                                    "event": "response",
                                    "content": response_text[:i+1],
                                    "timestamp": datetime.now().isoformat(),
                                    "is_complete": i == len(response_text) - 1
                                })
                            }
                            if i % 10 == 0:  # Small delay every 10 characters
                                await asyncio.sleep(0.02)
                        except Exception as stream_err:
                            print(f"[STREAM] Error streaming response: {stream_err}")
                            import traceback
                            traceback.print_exc()
                            break
                    
                    print(f"[STREAM] Response streaming complete (conversation)")
                    active_workflows[thread_id]["status"] = "completed"
                    return
                
                # For CBT protocol, continue with workflow
                user_intent = user_query if intent == "cbt_protocol" else f"{intent}: {user_query}"
                
            except Exception as intent_error:
                print(f"[STREAM] Intent classification failed: {intent_error}")
                import traceback
                traceback.print_exc()
                user_intent = user_query  # Fallback
            
            print(f"[STREAM] Creating graph...")
            # Create graph
            try:
                graph = await create_foundry_graph()
                print(f"[STREAM] Graph created successfully")
            except Exception as graph_error:
                error_msg = f"Failed to create graph: {str(graph_error)}"
                print(f"[STREAM] ERROR creating graph: {error_msg}")
                import traceback
                traceback.print_exc()
                yield {
                    "event": "error",
                    "data": json.dumps({"error": error_msg, "event": "error"})
                }
                return
            
            # Initial state
            from state import FoundryState
            workflow_info = active_workflows.get(thread_id, {})
            user_specifics = workflow_info.get("user_specifics", {})
            
            initial_state: FoundryState = {
                "user_intent": user_intent,
                "user_query": user_query,
                "user_specifics": user_specifics,
                "information_gathered": bool(user_specifics),
                "questions_for_user": None,
                "awaiting_user_response": False,
                "iteration_count": 0,
                "max_iterations": 10,
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
            
            config = {"configurable": {"thread_id": thread_id}}
            
            print(f"[STREAM] Starting graph execution...")
            # Stream events
            last_state = initial_state
            event_count = 0
            last_notes_count = 0  # Track notes to stream thinking
            
            async for event in graph.astream(initial_state, config):
                event_count += 1
                print(f"[STREAM] Received event #{event_count}: {list(event.keys())}")
                
                # Format event for SSE
                for node_name, node_state in event.items():
                    last_state = node_state
                    print(f"[STREAM] Processing node: {node_name}, iteration: {node_state.get('iteration_count', 0)}")
                    
                    # Stream thinking from agent notes (all intermediate thinking should be in thinking mode)
                    agent_notes = node_state.get('agent_notes', [])
                    if len(agent_notes) > last_notes_count:
                        # New notes added - stream them as thinking
                        new_notes = agent_notes[last_notes_count:]
                        for note in new_notes:
                            # Only stream notes that contain "Thinking:" as thinking events
                            if "Thinking:" in note.get('message', '') or "thinking" in note.get('message', '').lower():
                                thinking_content = note['message']
                                # Stream thinking character by character
                                for i in range(len(thinking_content)):
                                    try:
                                        yield {
                                            "event": "thinking",
                                            "data": json.dumps({
                                                "event": "thinking",
                                                "agent": note['agent'].value if hasattr(note['agent'], 'value') else str(note['agent']),
                                                "content": thinking_content[:i+1],
                                                "timestamp": note['timestamp'],
                                                "is_complete": i == len(thinking_content) - 1
                                            })
                                        }
                                        if i % 3 == 0:  # Small delay every 3 characters
                                            await asyncio.sleep(0.01)
                                    except Exception as stream_err:
                                        print(f"[STREAM] Error streaming thinking from note: {stream_err}")
                                        break
                        
                        last_notes_count = len(agent_notes)
                    
                    # Send state update
                    try:
                        yield {
                            "event": "state_update",
                            "data": json.dumps({
                                "event": "state_update",
                                "node": node_name,
                                "state": node_state,
                                "timestamp": datetime.now().isoformat()
                            })
                        }
                        print(f"[STREAM] Sent state_update for node: {node_name}")
                    except Exception as yield_error:
                        print(f"[STREAM] ERROR yielding state_update: {yield_error}")
                        import traceback
                        traceback.print_exc()
                    
                    # Check if halted (including awaiting user response to questions)
                    if node_state.get("is_halted") or node_state.get("awaiting_human_approval") or node_state.get("awaiting_user_response"):
                        halt_reason = "Awaiting human approval"
                        questions = node_state.get("questions_for_user", [])
                        
                        if node_state.get("awaiting_user_response") and questions:
                            halt_reason = "Awaiting user response to questions"
                            yield {
                                "event": "halted",
                                "data": json.dumps({
                                    "event": "halted",
                                    "state": node_state,
                                    "message": halt_reason,
                                    "questions": questions,
                                    "awaiting_user_response": True
                                })
                            }
                        else:
                            yield {
                                "event": "halted",
                                "data": json.dumps({
                                    "event": "halted",
                                    "state": node_state,
                                    "message": halt_reason
                                })
                            }
                        active_workflows[thread_id]["status"] = "halted"
                        # Update history (if available)
                        if HISTORY_AVAILABLE:
                            try:
                                await update_protocol_status(thread_id, "halted", state_snapshot=node_state)
                            except Exception as e:
                                print(f"[STREAM] Warning: Could not update history: {e}")
                        return
                    
                    # Check if approved
                    if node_state.get("is_approved"):
                        final_protocol = node_state.get("final_protocol") or node_state.get("current_draft", "")
                        yield {
                            "event": "completed",
                            "data": json.dumps({
                                "event": "completed",
                                "state": node_state,
                                "message": "Protocol finalized"
                            })
                        }
                        active_workflows[thread_id]["status"] = "completed"
                        # Update history with final protocol (if available)
                        if HISTORY_AVAILABLE:
                            try:
                                await update_protocol_status(thread_id, "completed", final_protocol=final_protocol, state_snapshot=node_state)
                            except Exception as e:
                                print(f"[STREAM] Warning: Could not update history: {e}")
                        return
            
            # If we didn't halt or complete, check final state
            if last_state and not (last_state.get("is_halted") or last_state.get("is_approved")):
                # Check if we should halt (e.g., max iterations)
                if last_state.get("iteration_count", 0) >= last_state.get("max_iterations", 10):
                    yield {
                        "event": "halted",
                        "data": json.dumps({
                            "event": "halted",
                            "state": last_state,
                            "message": "Max iterations reached"
                        })
                    }
                    active_workflows[thread_id]["status"] = "halted"
                    return
            
            # Final state
            final_state = await graph.ainvoke(initial_state, config)
            yield {
                "event": "completed",
                "data": json.dumps({
                    "event": "completed",
                    "state": final_state,
                    "message": "Protocol generation completed"
                })
            }
            active_workflows[thread_id]["status"] = "completed"
            
        except Exception as e:
            import traceback
            error_msg = f"Stream error: {str(e)}"
            print(f"[STREAM] EXCEPTION in event_generator: {error_msg}")
            traceback.print_exc()
            try:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": error_msg, "event": "error"})
                }
            except:
                pass
            if thread_id in active_workflows:
                active_workflows[thread_id]["status"] = "error"
    
    print(f"[STREAM] Returning EventSourceResponse for thread: {thread_id}")
    return EventSourceResponse(event_generator())
    
    return EventSourceResponse(event_generator())


@app.get("/api/protocols/{thread_id}/state")
async def get_protocol_state(thread_id: str):
    """
    Get current state from checkpoint.
    Used for human-in-the-loop interruption.
    """
    try:
        graph = await create_foundry_graph()
        checkpointer = await get_checkpointer()
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get state from checkpoint
        state = await checkpointer.aget(config)
        
        if not state:
            raise HTTPException(status_code=404, detail="Protocol not found")
        
        # Extract the actual state
        checkpoint_state = state.get("channel_values", {})
        
        return {
            "thread_id": thread_id,
            "state": checkpoint_state,
            "status": active_workflows.get(thread_id, {}).get("status", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/protocols/{thread_id}/approve")
async def approve_protocol(thread_id: str, request: ApproveRequest):
    """
    Human approves or edits the protocol.
    Resumes workflow from checkpoint with human input.
    Uses database checkpoint to resume exactly where it left off.
    """
    print(f"[APPROVE] Human approval received for thread: {thread_id}")
    try:
        graph = await create_foundry_graph()
        checkpointer = await get_checkpointer()
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state from checkpoint (this is the persisted state)
        checkpoint_state = await graph.aget_state(config)
        if not checkpoint_state:
            raise HTTPException(status_code=404, detail="Protocol not found in checkpoint")
        
        current_state = checkpoint_state.values
        
        print(f"[APPROVE] Resuming from checkpoint. Current state: halted={current_state.get('is_halted')}, draft_exists={bool(current_state.get('current_draft'))}")
        
        # Update state with human input - this updates the checkpoint
        updated_state = {
            **current_state,
            "is_halted": False,
            "awaiting_human_approval": False,
            "awaiting_user_response": False,
            "is_approved": True,
            "human_edited_draft": request.edited_draft or current_state.get('current_draft'),
            "human_feedback": request.feedback,
            "final_protocol": request.edited_draft or current_state.get('current_draft', ''),
            "last_updated": datetime.now().isoformat()
        }
        
        # Update the checkpoint with new state
        await graph.aupdate_state(config, updated_state)
        
        # Log to history (if available)
        if HISTORY_AVAILABLE:
            try:
                await update_protocol_status(
                    thread_id=thread_id,
                    status="approved",
                    final_protocol=updated_state.get("final_protocol"),
                    state_snapshot=updated_state
                )
            except Exception as history_err:
                print(f"[APPROVE] Warning: Could not log to history: {history_err}")
        
        # Fallback to workflow info
        active_workflows[thread_id]["final_protocol"] = updated_state.get("final_protocol")
        active_workflows[thread_id]["approved_at"] = datetime.now().isoformat()
        
        # Get final state from checkpoint
        final_state_checkpoint = await graph.aget_state(config)
        final_state = final_state_checkpoint.values if final_state_checkpoint else updated_state
        
        active_workflows[thread_id]["status"] = "approved"
        
        print(f"[APPROVE] Protocol approved and finalized. Final protocol length: {len(final_state.get('final_protocol', ''))}")
        
        return {
            "thread_id": thread_id,
            "status": "approved",
            "state": final_state
        }
    except Exception as e:
        print(f"[APPROVE] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/protocols")
async def list_protocols():
    """List all protocols"""
    return {
        "protocols": [
            {
                "thread_id": tid,
                "status": info["status"],
                "started_at": info["started_at"],
                "user_query": info["user_query"]
            }
            for tid, info in active_workflows.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

