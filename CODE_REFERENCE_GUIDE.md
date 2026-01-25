# Code Reference Guide - Personal MCP Chatbot

**Complete code navigation with file paths and line numbers. Ctrl+Click to jump to code locations.**

---

## 📍 Table of Contents

1. [Stack Architecture Overview](#stack-architecture-overview)
2. [Graph Definition & Workflow](#graph-definition--workflow)
3. [Checkpointing System](#checkpointing-system)
4. [All Checkpoint Save Points](#all-checkpoint-save-points)
5. [State Management](#state-management)
6. [API Endpoints](#api-endpoints)
7. [Agent Implementations](#agent-implementations)
8. [Human-in-the-Loop Flow](#human-in-the-loop-flow)
9. [Error Handling & Fallbacks](#error-handling--fallbacks)

---

## 🏗️ Stack Architecture Overview

### Entry Point: FastAPI Server
**File**: [`backend/main.py`](backend/main.py)
- **Line 37**: FastAPI app initialization
- **Line 40-46**: CORS middleware setup
- **Line 78-112**: `POST /api/protocols/create` - Creates workflow thread
- **Line 115-476**: `GET /api/protocols/{thread_id}/stream` - SSE streaming endpoint
- **Line 479-506**: `GET /api/protocols/{thread_id}/state` - Get state from checkpoint
- **Line 509-587**: `POST /api/protocols/{thread_id}/approve` - Human approval endpoint

### Graph Creation
**File**: [`backend/graph.py`](backend/graph.py)
- **Line 21-121**: `create_foundry_graph()` - Creates LangGraph workflow
- **Line 38**: `StateGraph(FoundryState)` - Graph initialization
- **Line 41-45**: Agent nodes added to graph
- **Line 76-77**: Halt and Approve nodes added
- **Line 80**: Entry point set to "supervisor"
- **Line 92-103**: Conditional routing from supervisor
- **Line 106-109**: All workers return to supervisor
- **Line 112-113**: Terminal nodes (halt, approve)
- **Line 116**: Checkpointer retrieved
- **Line 119**: Graph compiled with checkpointer

### Database & Checkpointing
**File**: [`backend/database.py`](backend/database.py)
- **Line 25**: Database URL from environment
- **Line 28**: Database type detection (PostgreSQL vs SQLite)
- **Line 31-36**: Async engine creation
- **Line 44-104**: `get_checkpointer()` - Checkpointer creation with fallbacks

### State Schema
**File**: [`backend/state.py`](backend/state.py)
- **Line 71-126**: `FoundryState` TypedDict definition
- **Line 35-40**: `AgentNote` structure
- **Line 43-50**: `DraftVersion` structure
- **Line 52-59**: `SafetyReview` structure
- **Line 61-69**: `ClinicalReview` structure

---

## 🔄 Graph Definition & Workflow

### Graph Structure
**File**: [`backend/graph.py`](backend/graph.py)

#### Node Definitions
- **Line 31**: Supervisor agent created
- **Line 32**: Draftsman agent created
- **Line 33**: Safety Guardian agent created
- **Line 34**: Clinical Critic agent created
- **Line 35**: Debate Moderator agent created
- **Line 48-60**: `halt_node()` - Halt function (sets `is_halted = True`)
- **Line 63-74**: `approve_node()` - Approve function (sets `is_approved = True`)

#### Graph Edges
- **Line 80**: Entry point: `workflow.set_entry_point("supervisor")`
- **Line 92-103**: Conditional edges from supervisor (routes based on `next_action`)
- **Line 106**: `workflow.add_edge("draftsman", "supervisor")`
- **Line 107**: `workflow.add_edge("safety_guardian", "supervisor")`
- **Line 108**: `workflow.add_edge("clinical_critic", "supervisor")`
- **Line 109**: `workflow.add_edge("debate_moderator", "supervisor")`
- **Line 112**: `workflow.add_edge("halt", END)`
- **Line 113**: `workflow.add_edge("approve", END)`

#### Routing Logic
**File**: [`backend/graph.py`](backend/graph.py)
- **Line 83-90**: `route_decision()` - Extracts `next_action` from state for routing

#### Graph Compilation
**File**: [`backend/graph.py`](backend/graph.py)
- **Line 116**: `checkpointer = await get_checkpointer()`
- **Line 119**: `app = workflow.compile(checkpointer=checkpointer)` - **THIS IS WHERE CHECKPOINTING IS ENABLED**

---

## 💾 Checkpointing System

### Checkpointer Creation
**File**: [`backend/database.py`](backend/database.py)

#### Fallback Chain (in order)
1. **Line 52-58**: Try `AsyncSqlAlchemySaver` (works with SQLite and PostgreSQL)
   - Import: `from langgraph.checkpoint.sqlalchemy import AsyncSqlAlchemySaver`
   - Creation: `AsyncSqlAlchemySaver(engine)`
   - Setup: `await checkpointer.setup()`

2. **Line 65-71**: Try alternative import path for `AsyncSqlAlchemySaver`
   - Import: `from langgraph_checkpoint.sqlalchemy import AsyncSqlAlchemySaver`

3. **Line 76-93**: If PostgreSQL, try `AsyncPostgresSaver`
   - **Line 79**: Import: `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver`
   - **Line 80**: Creation: `AsyncPostgresSaver.from_conn_string(DATABASE_URL)`
   - **Line 87**: Alternative: `from langgraph.checkpoint.postgres import AsyncPostgresSaver`

4. **Line 96-101**: Fallback to `MemorySaver` (in-memory, no persistence)
   - Import: `from langgraph.checkpoint.memory import MemorySaver`
   - Creation: `MemorySaver()`

### Database Configuration
**File**: [`backend/database.py`](backend/database.py)
- **Line 25**: `DATABASE_URL` from environment (default: PostgreSQL in Docker)
- **Line 28**: `IS_POSTGRES` detection
- **Line 31-36**: Async engine creation (PostgreSQL uses `asyncpg`, SQLite uses `aiosqlite`)

### Checkpointer Usage in Graph
**File**: [`backend/graph.py`](backend/graph.py)
- **Line 13**: Import: `from database import get_checkpointer`
- **Line 116**: `checkpointer = await get_checkpointer()`
- **Line 119**: `app = workflow.compile(checkpointer=checkpointer)` - **Checkpointer attached here**

---

## 📍 All Checkpoint Save Points

### Automatic Checkpointing (LangGraph)
**LangGraph automatically checkpoints after EVERY node execution when checkpointer is attached.**

#### When Checkpointing Happens:
1. **After Supervisor Node** - [`backend/agents/supervisor.py`](backend/agents/supervisor.py:191-197)
   - State updated with routing decision
   - Checkpointed automatically by LangGraph

2. **After Draftsman Node** - [`backend/agents/draftsman.py`](backend/agents/draftsman.py)
   - Draft created/updated
   - Checkpointed automatically

3. **After Safety Guardian Node** - [`backend/agents/safety_guardian.py`](backend/agents/safety_guardian.py)
   - Safety review completed
   - Checkpointed automatically

4. **After Clinical Critic Node** - [`backend/agents/clinical_critic.py`](backend/agents/clinical_critic.py)
   - Clinical review completed
   - Checkpointed automatically

5. **After Debate Moderator Node** - [`backend/agents/debate_moderator.py`](backend/agents/debate_moderator.py)
   - Debate completed
   - Checkpointed automatically

6. **After Halt Node** - [`backend/graph.py`](backend/graph.py:48-60)
   - `is_halted = True` set
   - Checkpointed automatically

7. **After Approve Node** - [`backend/graph.py`](backend/graph.py:63-74)
   - `is_approved = True` set
   - Checkpointed automatically

### Manual Checkpoint Updates

#### 1. Human Approval Checkpoint Update
**File**: [`backend/main.py`](backend/main.py)
- **Line 524**: Get state from checkpoint: `checkpoint_state = await graph.aget_state(config)`
- **Line 528**: Extract current state: `current_state = checkpoint_state.values`
- **Line 533-543**: Update state with human input
- **Line 546**: **UPDATE CHECKPOINT**: `await graph.aupdate_state(config, updated_state)`
- **Line 573**: Get final state: `final_state_checkpoint = await graph.aget_state(config)`

#### 2. State Retrieval from Checkpoint
**File**: [`backend/main.py`](backend/main.py)
- **Line 487**: Get checkpointer: `checkpointer = await get_checkpointer()`
- **Line 492**: Get state: `state = await checkpointer.aget(config)`
- **Line 498**: Extract state: `checkpoint_state = state.get("channel_values", {})`

### Checkpoint Configuration
**File**: [`backend/main.py`](backend/main.py)
- **Line 327**: Config creation: `config = {"configurable": {"thread_id": thread_id}}`
- **Line 335**: Graph streaming: `async for event in graph.astream(initial_state, config)`
- **Line 489**: Config for state retrieval: `config = {"configurable": {"thread_id": thread_id}}`
- **Line 521**: Config for approval: `config = {"configurable": {"thread_id": thread_id}}`

---

## 📊 State Management

### State Schema Definition
**File**: [`backend/state.py`](backend/state.py)

#### Core State Structure
- **Line 71-126**: `FoundryState` TypedDict
  - **Line 79-84**: User input fields
  - **Line 87-91**: Workflow control fields
  - **Line 94-97**: Draft management (Blackboard pattern)
  - **Line 100**: Agent communication scratchpad
  - **Line 103-104**: Review results
  - **Line 107-108**: Debate transcript
  - **Line 111-112**: Learning patterns
  - **Line 115-117**: Metadata
  - **Line 120-122**: Human-in-the-loop fields
  - **Line 125**: Routing decision

#### State Initialization
**File**: [`backend/main.py`](backend/main.py)
- **Line 291-325**: Initial state creation for workflow
  - **Line 295**: `initial_state: FoundryState = {...}`
  - All fields initialized with defaults

**File**: [`backend/graph.py`](backend/graph.py)
- **Line 145-171**: Initial state in `run_foundry_workflow()`

### State Updates in Agents

#### Supervisor State Update
**File**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Line 191-197**: Returns updated state with:
  - `next_action`: Routing decision
  - `agent_notes`: Thinking and decision notes
  - `current_agent`: AgentRole.SUPERVISOR
  - `last_updated`: Timestamp

#### Draftsman State Update
**File**: [`backend/agents/draftsman.py`](backend/agents/draftsman.py)
- Updates `current_draft` (shared document)
- Adds to `draft_versions`
- Increments `current_version`
- Adds `agent_notes`

#### Safety Guardian State Update
**File**: [`backend/agents/safety_guardian.py`](backend/agents/safety_guardian.py)
- Updates `safety_review` with:
  - Status (passed/flagged/critical)
  - Concerns list
  - Recommendations list

#### Clinical Critic State Update
**File**: [`backend/agents/clinical_critic.py`](backend/agents/clinical_critic.py)
- Updates `clinical_review` with:
  - Status (approved/needs_revision/rejected)
  - Scores (empathy, tone, structure)
  - Feedback list

#### Debate Moderator State Update
**File**: [`backend/agents/debate_moderator.py`](backend/agents/debate_moderator.py)
- Updates `agent_debate` with debate transcript
- Sets `debate_complete = True`

---

## 🌐 API Endpoints

### 1. Create Protocol
**File**: [`backend/main.py`](backend/main.py)
- **Line 78-112**: `POST /api/protocols/create`
  - **Line 85**: Creates `thread_id` (UUID)
  - **Line 89-94**: Stores workflow info in `active_workflows`
  - **Line 97-106**: Logs to history (non-blocking)
  - **Line 108-112**: Returns `thread_id` immediately

### 2. Stream Protocol
**File**: [`backend/main.py`](backend/main.py)
- **Line 115-476**: `GET /api/protocols/{thread_id}/stream`
  - **Line 123**: `event_generator()` async function
  - **Line 144**: Intent classification
  - **Line 172-263**: Handle non-CBT requests (question/conversation)
  - **Line 277**: Create graph
  - **Line 291-325**: Initialize state
  - **Line 327**: Create config with `thread_id`
  - **Line 335**: **Stream graph execution**: `async for event in graph.astream(initial_state, config)`
  - **Line 340-389**: Process events and stream to client
  - **Line 392-409**: Handle halt event
  - **Line 412-429**: Handle completion event
  - **Line 474**: Return `EventSourceResponse` (SSE)

### 3. Get State
**File**: [`backend/main.py`](backend/main.py)
- **Line 479-506**: `GET /api/protocols/{thread_id}/state`
  - **Line 486**: Create graph
  - **Line 487**: Get checkpointer
  - **Line 489**: Create config
  - **Line 492**: **Get state from checkpoint**: `state = await checkpointer.aget(config)`
  - **Line 498**: Extract state: `checkpoint_state = state.get("channel_values", {})`
  - **Line 500-504**: Return state

### 4. Approve Protocol
**File**: [`backend/main.py`](backend/main.py)
- **Line 509-587**: `POST /api/protocols/{thread_id}/approve`
  - **Line 518**: Create graph
  - **Line 519**: Get checkpointer
  - **Line 521**: Create config
  - **Line 524**: **Get state from checkpoint**: `checkpoint_state = await graph.aget_state(config)`
  - **Line 528**: Extract current state
  - **Line 533-543**: Update state with human input
  - **Line 546**: **UPDATE CHECKPOINT**: `await graph.aupdate_state(config, updated_state)`
  - **Line 549-558**: Log to history
  - **Line 573**: Get final state from checkpoint
  - **Line 578-582**: Return final state

---

## 🤖 Agent Implementations

### Supervisor Agent
**File**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Line 12**: `create_supervisor_agent(llm)` - Factory function
- **Line 15**: `supervisor_node(state: FoundryState)` - Node function
- **Line 20**: Logging iteration count
- **Line 23-45**: Decision logic (approved, halted, max iterations, loop detection)
- **Line 48-100**: Build context and prompt for LLM
- **Line 103-136**: Get LLM response and extract thinking/decision
- **Line 138-143**: Create thinking note
- **Line 146-162**: **Fallback logic** if invalid decision
- **Line 191-197**: Return updated state with routing decision

### Draftsman Agent
**File**: [`backend/agents/draftsman.py`](backend/agents/draftsman.py)
- **Line 12**: `create_draftsman_agent(llm)` - Factory function
- **Line 15**: `draftsman_node(state: FoundryState)` - Node function
- Creates/edits `current_draft` (shared document)
- Updates `draft_versions` and `current_version`
- Adds `agent_notes`

### Safety Guardian Agent
**File**: [`backend/agents/safety_guardian.py`](backend/agents/safety_guardian.py)
- **Line 12**: `create_safety_guardian_agent(llm)` - Factory function
- Reviews `current_draft` for safety concerns
- Updates `safety_review` with status, concerns, recommendations

### Clinical Critic Agent
**File**: [`backend/agents/clinical_critic.py`](backend/agents/clinical_critic.py)
- **Line 12**: `create_clinical_critic_agent(llm)` - Factory function
- Evaluates `current_draft` for clinical quality
- Updates `clinical_review` with scores and feedback

### Debate Moderator Agent
**File**: [`backend/agents/debate_moderator.py`](backend/agents/debate_moderator.py)
- **Line 12**: `create_debate_moderator_agent(llm)` - Factory function
- Facilitates internal debate
- Updates `agent_debate` and sets `debate_complete = True`

---

## 👤 Human-in-the-Loop Flow

### 1. Workflow Halts
**File**: [`backend/graph.py`](backend/graph.py)
- **Line 48-60**: `halt_node()` function
  - Sets `is_halted = True`
  - Sets `awaiting_human_approval = True`
  - **State automatically checkpointed by LangGraph**

**File**: [`backend/main.py`](backend/main.py)
- **Line 392-409**: Detects halt in stream
  - **Line 392**: Check: `if node_state.get("is_halted") or node_state.get("awaiting_human_approval")`
  - **Line 394-401**: Stream `halted` event to frontend
  - **Line 402**: Update workflow status
  - **Line 404-408**: Log to history

### 2. Human Reviews State
**File**: [`backend/main.py`](backend/main.py)
- **Line 479-506**: `GET /api/protocols/{thread_id}/state`
  - **Line 492**: Get state from checkpoint
  - **Line 498**: Extract state
  - **Line 500-504**: Return state to frontend

### 3. Human Approves/Edits
**File**: [`backend/main.py`](backend/main.py)
- **Line 509-587**: `POST /api/protocols/{thread_id}/approve`
  - **Line 524**: Get current state from checkpoint
  - **Line 533-543**: Update state with human input:
    - `is_halted = False`
    - `awaiting_human_approval = False`
    - `is_approved = True`
    - `human_edited_draft = request.edited_draft`
    - `human_feedback = request.feedback`
    - `final_protocol = request.edited_draft or current_draft`
  - **Line 546**: **UPDATE CHECKPOINT**: `await graph.aupdate_state(config, updated_state)`
  - **Line 573**: Get final state from checkpoint
  - **Line 578-582**: Return final state

---

## 🛡️ Error Handling & Fallbacks

### 1. Checkpointer Fallbacks
**File**: [`backend/database.py`](backend/database.py)
- **Line 52-58**: Try AsyncSqlAlchemySaver
- **Line 65-71**: Try alternative import
- **Line 76-93**: Try AsyncPostgresSaver (if PostgreSQL)
- **Line 96-101**: Fallback to MemorySaver

### 2. Supervisor Routing Fallback
**File**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Line 146-162**: If invalid decision, use strict workflow sequence
  - **Line 149**: No draft → `draftsman`
  - **Line 151**: No safety review → `safety_guardian`
  - **Line 153**: Safety issues → `draftsman`
  - **Line 155**: No clinical review → `clinical_critic`
  - **Line 157**: Clinical issues → `draftsman`
  - **Line 159**: Debate incomplete → `debate_moderator`
  - **Line 162**: Otherwise → `halt`

### 3. Loop Detection
**File**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Line 33-42**: After 5 iterations, check for repeated decisions
  - **Line 35-39**: Get recent decisions from agent notes
  - **Line 40**: If same decision 3x → halt

### 4. Max Iterations
**File**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Line 29-31**: If `iteration_count >= max_iterations` → halt

**File**: [`backend/main.py`](backend/main.py)
- **Line 434**: Check max iterations in stream

### 5. Intent Classification Fallback
**File**: [`backend/main.py`](backend/main.py)
- **Line 268-272**: If intent classification fails, use `user_query` as `user_intent`

### 6. History Logging Fallback
**File**: [`backend/main.py`](backend/main.py)
- **Line 24-35**: History module wrapped in try-except
- **Line 97-106**: Non-blocking history logging
- **Line 404-408**: Non-blocking history update
- **Line 549-558**: Non-blocking history update on approval

### 7. Stream Error Handling
**File**: [`backend/main.py`](backend/main.py)
- **Line 458-471**: Try-except around entire event generator
  - **Line 464-467**: Stream error event
  - **Line 470**: Update workflow status to "error"

### 8. Graph Creation Error
**File**: [`backend/main.py`](backend/main.py)
- **Line 276-288**: Try-except for graph creation
  - **Line 284-287**: Stream error event if graph creation fails

---

## 🔍 Key Code Locations Summary

### Checkpointing
- **Checkpointer Creation**: [`backend/database.py:44-104`](backend/database.py#L44-L104)
- **Graph Compilation with Checkpointer**: [`backend/graph.py:116-119`](backend/graph.py#L116-L119)
- **Get State from Checkpoint**: [`backend/main.py:492`](backend/main.py#L492)
- **Update Checkpoint**: [`backend/main.py:546`](backend/main.py#L546)
- **Get State via Graph**: [`backend/main.py:524`](backend/main.py#L524)

### Graph Definition
- **Graph Creation**: [`backend/graph.py:21-121`](backend/graph.py#L21-L121)
- **Node Definitions**: [`backend/graph.py:31-77`](backend/graph.py#L31-L77)
- **Edge Definitions**: [`backend/graph.py:80-113`](backend/graph.py#L80-L113)
- **Routing Logic**: [`backend/graph.py:83-90`](backend/graph.py#L83-L90)

### State Management
- **State Schema**: [`backend/state.py:71-126`](backend/state.py#L71-L126)
- **State Initialization**: [`backend/main.py:291-325`](backend/main.py#L291-L325)
- **State Updates**: Each agent file (supervisor.py, draftsman.py, etc.)

### API Endpoints
- **Create Protocol**: [`backend/main.py:78-112`](backend/main.py#L78-L112)
- **Stream Protocol**: [`backend/main.py:115-476`](backend/main.py#L115-L476)
- **Get State**: [`backend/main.py:479-506`](backend/main.py#L479-L506)
- **Approve Protocol**: [`backend/main.py:509-587`](backend/main.py#L509-L587)

### Agents
- **Supervisor**: [`backend/agents/supervisor.py`](backend/agents/supervisor.py)
- **Draftsman**: [`backend/agents/draftsman.py`](backend/agents/draftsman.py)
- **Safety Guardian**: [`backend/agents/safety_guardian.py`](backend/agents/safety_guardian.py)
- **Clinical Critic**: [`backend/agents/clinical_critic.py`](backend/agents/clinical_critic.py)
- **Debate Moderator**: [`backend/agents/debate_moderator.py`](backend/agents/debate_moderator.py)

### Fallbacks
- **Checkpointer Fallbacks**: [`backend/database.py:44-104`](backend/database.py#L44-L104)
- **Routing Fallback**: [`backend/agents/supervisor.py:146-162`](backend/agents/supervisor.py#L146-L162)
- **Loop Detection**: [`backend/agents/supervisor.py:33-42`](backend/agents/supervisor.py#L33-L42)

---

## 📝 Important Notes

1. **Automatic Checkpointing**: LangGraph automatically checkpoints after EVERY node execution when checkpointer is attached at graph compilation.

2. **Checkpoint Key**: Uses `thread_id` from config: `{"configurable": {"thread_id": thread_id}}`

3. **State Retrieval**: Two methods:
   - `checkpointer.aget(config)` - Direct checkpointer access
   - `graph.aget_state(config)` - Via graph (preferred)

4. **State Updates**: Use `graph.aupdate_state(config, updated_state)` to update checkpoint

5. **All Nodes Checkpointed**: Supervisor, Draftsman, Safety Guardian, Clinical Critic, Debate Moderator, Halt, Approve - all checkpointed automatically.

6. **Human-in-the-Loop**: State retrieved from checkpoint → Human edits → State updated in checkpoint → Workflow can resume (though currently completes on approval).

---

**Use Ctrl+Click on file paths to navigate directly to code locations!**


