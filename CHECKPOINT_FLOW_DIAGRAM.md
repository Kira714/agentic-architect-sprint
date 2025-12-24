# Checkpoint Flow Diagram - Visual Guide

## 🔄 Complete Checkpoint Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW EXECUTION                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. GRAPH CREATION                                                │
│    File: backend/graph.py:21-121                                │
│    ┌──────────────────────────────────────────────┐              │
│    │ create_foundry_graph()                       │              │
│    │  • Create agents (line 31-35)                │              │
│    │  • Add nodes to graph (line 41-77)            │              │
│    │  • Define edges (line 80-113)                 │              │
│    │  • Get checkpointer (line 116)               │              │
│    │  • Compile with checkpointer (line 119) ⭐   │              │
│    └──────────────────────────────────────────────┘              │
│                                                                  │
│    ⭐ THIS IS WHERE CHECKPOINTING IS ENABLED                    │
│    Line 119: app = workflow.compile(checkpointer=checkpointer)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. WORKFLOW START                                                │
│    File: backend/main.py:335                                     │
│    ┌──────────────────────────────────────────────┐              │
│    │ graph.astream(initial_state, config)          │              │
│    │  • config = {"configurable": {"thread_id"}}   │              │
│    │  • Initial state created (line 291-325)        │              │
│    └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SUPERVISOR NODE EXECUTION                                    │
│    File: backend/agents/supervisor.py:15-197                     │
│    ┌──────────────────────────────────────────────┐              │
│    │ supervisor_node(state)                        │              │
│    │  • Analyze state                              │              │
│    │  • Make routing decision                       │              │
│    │  • Return updated state (line 191-197)        │              │
│    └──────────────────────────────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│    ⭐ AUTOMATIC CHECKPOINT (LangGraph)                          │
│    State saved to database with thread_id                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. WORKER NODE EXECUTION (Draftsman/Safety/Clinical/Debate)    │
│    Files:                                                        │
│    • backend/agents/draftsman.py                                 │
│    • backend/agents/safety_guardian.py                           │
│    • backend/agents/clinical_critic.py                          │
│    • backend/agents/debate_moderator.py                          │
│    ┌──────────────────────────────────────────────┐              │
│    │ worker_node(state)                            │              │
│    │  • Process task                                │              │
│    │  • Update state                                │              │
│    │  • Return updated state                        │              │
│    └──────────────────────────────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│    ⭐ AUTOMATIC CHECKPOINT (LangGraph)                          │
│    State saved to database with thread_id                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. HALT NODE EXECUTION                                           │
│    File: backend/graph.py:48-60                                  │
│    ┌──────────────────────────────────────────────┐              │
│    │ halt_node(state)                               │              │
│    │  • Set is_halted = True (line 56)             │              │
│    │  • Set awaiting_human_approval = True (line 57)│              │
│    │  • Return updated state                        │              │
│    └──────────────────────────────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│    ⭐ AUTOMATIC CHECKPOINT (LangGraph)                          │
│    State saved to database with thread_id                        │
│                                                                  │
│    File: backend/main.py:392-409                                 │
│    • Stream "halted" event to frontend                           │
│    • Update workflow status to "halted"                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. HUMAN REVIEW (Frontend)                                       │
│    • User sees draft                                             │
│    • User can edit draft                                         │
│    • User clicks "Approve"                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. GET STATE FROM CHECKPOINT                                     │
│    File: backend/main.py:479-506                                 │
│    Endpoint: GET /api/protocols/{thread_id}/state               │
│    ┌──────────────────────────────────────────────┐              │
│    │ get_protocol_state(thread_id)                │              │
│    │  • Create graph (line 486)                    │              │
│    │  • Get checkpointer (line 487)                │              │
│    │  • Create config (line 489)                   │              │
│    │  • Get state (line 492) ⭐                    │              │
│    │    state = await checkpointer.aget(config)    │              │
│    │  • Extract state (line 498)                   │              │
│    │  • Return state to frontend                    │              │
│    └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. HUMAN APPROVAL                                               │
│    File: backend/main.py:509-587                                 │
│    Endpoint: POST /api/protocols/{thread_id}/approve             │
│    ┌──────────────────────────────────────────────┐              │
│    │ approve_protocol(thread_id, request)         │              │
│    │  • Create graph (line 518)                    │              │
│    │  • Get checkpointer (line 519)                │              │
│    │  • Create config (line 521)                    │              │
│    │  • Get state from checkpoint (line 524) ⭐    │              │
│    │    checkpoint_state = await graph.aget_state()│              │
│    │  • Extract current state (line 528)            │              │
│    │  • Update state with human input (line 533-543)│              │
│    │  • UPDATE CHECKPOINT (line 546) ⭐⭐⭐         │              │
│    │    await graph.aupdate_state(config, updated) │              │
│    │  • Get final state (line 573)                  │              │
│    │  • Return final state                          │              │
│    └──────────────────────────────────────────────┘              │
│                                                                  │
│    ⭐⭐⭐ THIS IS WHERE CHECKPOINT IS UPDATED                    │
│    Human edits are persisted to checkpoint                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. WORKFLOW COMPLETE                                             │
│    • is_approved = True                                          │
│    • final_protocol set                                          │
│    • State checkpointed one final time                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📍 Checkpoint Save Points (All Locations)

### Automatic Checkpoints (LangGraph)

1. **After Supervisor Node**
   - **File**: `backend/agents/supervisor.py:191-197`
   - **Trigger**: Supervisor returns updated state
   - **Content**: Routing decision, agent notes, iteration count

2. **After Draftsman Node**
   - **File**: `backend/agents/draftsman.py` (end of function)
   - **Trigger**: Draftsman returns updated state
   - **Content**: Current draft, draft versions, agent notes

3. **After Safety Guardian Node**
   - **File**: `backend/agents/safety_guardian.py` (end of function)
   - **Trigger**: Safety Guardian returns updated state
   - **Content**: Safety review results, concerns, recommendations

4. **After Clinical Critic Node**
   - **File**: `backend/agents/clinical_critic.py` (end of function)
   - **Trigger**: Clinical Critic returns updated state
   - **Content**: Clinical review results, scores, feedback

5. **After Debate Moderator Node**
   - **File**: `backend/agents/debate_moderator.py` (end of function)
   - **Trigger**: Debate Moderator returns updated state
   - **Content**: Debate transcript, debate_complete flag

6. **After Halt Node**
   - **File**: `backend/graph.py:48-60`
   - **Trigger**: Halt node returns updated state
   - **Content**: is_halted=True, awaiting_human_approval=True

7. **After Approve Node**
   - **File**: `backend/graph.py:63-74`
   - **Trigger**: Approve node returns updated state
   - **Content**: is_approved=True, final_protocol

### Manual Checkpoint Updates

1. **Human Approval Update**
   - **File**: `backend/main.py:546`
   - **Code**: `await graph.aupdate_state(config, updated_state)`
   - **Trigger**: Human approves/edits protocol
   - **Content**: Human edits, feedback, final protocol

---

## 🔍 Checkpoint Retrieval Points

1. **Get State for Human Review**
   - **File**: `backend/main.py:492`
   - **Code**: `state = await checkpointer.aget(config)`
   - **Purpose**: Retrieve state for frontend display

2. **Get State for Approval**
   - **File**: `backend/main.py:524`
   - **Code**: `checkpoint_state = await graph.aget_state(config)`
   - **Purpose**: Get current state before updating with human input

3. **Get Final State After Approval**
   - **File**: `backend/main.py:573`
   - **Code**: `final_state_checkpoint = await graph.aget_state(config)`
   - **Purpose**: Get updated state after human approval

---

## 🎯 Key Code Locations for Checkpointing

### Checkpointer Creation
- **File**: `backend/database.py:44-104`
- **Function**: `get_checkpointer()`
- **Returns**: Checkpointer instance (AsyncSqlAlchemySaver, AsyncPostgresSaver, or MemorySaver)

### Graph Compilation with Checkpointer
- **File**: `backend/graph.py:116-119`
- **Code**:
  ```python
  checkpointer = await get_checkpointer()
  app = workflow.compile(checkpointer=checkpointer)
  ```
- **This enables automatic checkpointing**

### Checkpoint Retrieval
- **File**: `backend/main.py:492`
- **Code**: `state = await checkpointer.aget(config)`
- **Alternative**: `backend/main.py:524` - `await graph.aget_state(config)`

### Checkpoint Update
- **File**: `backend/main.py:546`
- **Code**: `await graph.aupdate_state(config, updated_state)`
- **This is the ONLY manual checkpoint update**

---

## 📊 Checkpoint Data Structure

Each checkpoint contains:
- **thread_id**: Unique identifier (from config)
- **channel_values**: Complete FoundryState object
  - All agent notes
  - Current draft
  - All reviews (safety, clinical)
  - Debate transcript
  - Workflow metadata
  - Human input (if any)

---

## 🔄 Checkpoint Flow Summary

1. **Graph Compiled** → Checkpointer attached → Automatic checkpointing enabled
2. **Each Node Executes** → State updated → **AUTOMATIC CHECKPOINT**
3. **Workflow Halts** → State checkpointed → Frontend retrieves state
4. **Human Reviews** → Gets state from checkpoint
5. **Human Approves** → Updates checkpoint with human input
6. **Workflow Complete** → Final state checkpointed

**Every node execution = One checkpoint save point!**


