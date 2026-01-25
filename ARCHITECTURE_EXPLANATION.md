# Personal MCP Chatbot - Complete Technical Explanation

## 🎯 Project Overview

**Personal MCP Chatbot** is a production-ready, autonomous multi-agent system that intelligently designs, critiques, and refines protocols and responses through rigorous internal debate and self-correction before presenting results to humans.

**Core Purpose**: Act as a "personal assistant" - autonomously creating evidence-based protocols that are safe, empathetic, and clinically sound, with human oversight at the final approval stage.

---

## 🏗️ Technical Architecture

### High-Level Architecture Stack

```
┌─────────────────────────────────────────────────────────┐
│              USER INTERFACE LAYER                       │
│  • React Dashboard (Real-time streaming, Human-in-loop) │
│  • MCP Server (Machine-to-Machine via Model Context Protocol) │
└──────────────────┬──────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────┐
│              API LAYER (FastAPI)                         │
│  • POST /api/protocols/create (creates thread_id)       │
│  • GET /api/protocols/{id}/stream (SSE streaming)       │
│  • POST /api/protocols/{id}/approve (resumes workflow)   │
│  • GET /api/protocols/{id}/state (gets checkpoint state)│
└───────────────────┬──────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────┐
│        LANGGRAPH WORKFLOW (Supervisor-Worker)           │
│  • Supervisor (Orchestrator)                             │
│  • Draftsman (Exercise Creator)                         │
│  • Safety Guardian (Safety Reviewer)                     │
│  • Clinical Critic (Quality Evaluator)                   │
│  • Debate Moderator (Internal Refinement)                │
│  • Halt (Human Review)                                   │
│  • Approve (Finalize)                                    │
└───────────────────┬──────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────┐
│     STATE MANAGEMENT (Blackboard Pattern)                │
│  • FoundryState (Shared State)                           │
│  • All agents read/write to same state                    │
└───────────────────┬──────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────┐
│           PERSISTENCE LAYER                              │
│  • LangGraph Checkpointer (PostgreSQL/SQLite)             │
│  • Protocol History Table                                │
│  • Every node execution checkpointed                      │
└──────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- **Python 3.10+**: Core language
- **LangGraph**: Workflow orchestration and checkpointing (critical for state persistence)
- **LangChain**: LLM integration and agent framework
- **FastAPI**: REST API with Server-Sent Events (SSE) for real-time streaming
- **SQLAlchemy**: Async ORM for database operations
- **PostgreSQL**: Primary database (with SQLite fallback for development)
- **asyncpg**: PostgreSQL async driver

**Frontend:**
- **React 18**: UI framework with TypeScript
- **Vite**: Build tool
- **react-markdown**: Markdown rendering for protocols

**MCP Integration:**
- **mcp-python SDK**: Model Context Protocol implementation for machine-to-machine communication

**LLM:**
- **OpenAI GPT-4o-mini**: Primary LLM (configurable via `OPENAI_MODEL`)

---

## 🤖 Multi-Agent System Architecture

### Supervisor-Worker Pattern (NOT a Linear Chain)

The system uses a **Supervisor-Worker pattern** with dynamic routing, NOT a simple linear chain. This enables:
- **Self-correction**: Agents can loop back for revisions
- **Dynamic routing**: Supervisor analyzes state and routes intelligently
- **Iterative refinement**: Can go through multiple cycles until quality is met

### Agent Roles & Responsibilities

#### 1. **Supervisor Agent** (Orchestrator)
- **Role**: Central decision-maker and workflow router
- **Key Features**:
  - Analyzes complete workflow state with maximum precision
  - Makes evidence-based routing decisions
  - **Loop Detection**: Detects infinite loops (if same decision repeated 3+ times after 5 iterations)
  - **Max Iteration Protection**: Halts at max_iterations (default: 10)
  - **Strict Workflow Compliance**: Zero tolerance for deviations
- **Routing Logic**:
  1. No draft → `draftsman`
  2. Draft exists, no safety review → `safety_guardian`
  3. Safety = critical/flagged → `draftsman` (fix safety)
  4. Safety = passed, no clinical review → `clinical_critic`
  5. Clinical = needs_revision/rejected → `draftsman` (fix quality)
  6. Both passed, debate incomplete → `debate_moderator`
  7. All complete → `halt`
  8. Max iterations → `halt`
- **Fallback Logic**: If LLM returns invalid decision, uses strict workflow sequence based on state

#### 2. **Draftsman Agent** (Exercise Creator)
- **Role**: Creates and revises CBT exercise drafts
- **Key Features**:
  - Creates evidence-based, professional CBT exercises
  - **Shared Document Editing**: Edits `current_draft` (Blackboard pattern)
  - Incorporates feedback from reviews and debate
  - Ensures exercises surpass medical standards
  - Includes all required clinical components (SUDS, progression criteria, safety behaviors)
- **System Prompt**: Expert-level CBT knowledge, clinical rigor, evidence-based protocols
- **Output**: Practice-ready CBT exercises with proper markdown formatting

#### 3. **Safety Guardian Agent** (Safety Reviewer)
- **Role**: Comprehensive safety review with zero tolerance
- **Key Features**:
  - Reviews for self-harm risks and triggers
  - Checks for medical advice exceeding therapeutic boundaries
  - Identifies dangerous or harmful instructions
  - Ensures safety disclaimers and crisis resources
  - Verifies contraindications and red flags
- **Output**: Safety review with status (`passed`/`flagged`/`critical`), concerns, and recommendations

#### 4. **Clinical Critic Agent** (Quality Evaluator)
- **Role**: Rigorous clinical quality evaluation
- **Key Features**:
  - Evaluates empathy, tone, and structure (0-10 scales)
  - Assesses therapeutic effectiveness
  - Verifies evidence-based foundation
  - Ensures clinical completeness
  - Provides specific, actionable feedback
- **Output**: Clinical review with scores and feedback

#### 5. **Debate Moderator Agent** (Internal Refinement)
- **Role**: Facilitates systematic internal debate
- **Key Features**:
  - Orchestrates evidence-based debate between agents
  - Ensures all clinical concerns are addressed
  - Reaches consensus on refinements needed
  - Final quality check before human review
- **Output**: Debate transcript with consensus and refinements

### Workflow Graph Structure

```
Supervisor (Entry Point)
    │
    ├─→ Draftsman ──┐
    ├─→ Safety Guardian ──┤
    ├─→ Clinical Critic ──┤
    ├─→ Debate Moderator ──┤
    │                     │
    │                     └─→ Supervisor (All return here)
    │
    ├─→ Halt (Terminal - Human Review)
    └─→ Approve (Terminal - Finalize)
```

**Key Points:**
- All worker agents return to Supervisor after completing tasks
- Supervisor makes routing decision based on state
- Enables iterative refinement (e.g., Safety Guardian flags issue → Supervisor routes back to Draftsman)
- Halt and Approve are terminal nodes (workflow ends)

---

## 📊 State Management: Blackboard Pattern

### FoundryState Structure

The system uses a **Blackboard Pattern** - a rich, structured shared state where all agents read from and write to the same state object.

**State Components:**

1. **User Input**
   - `user_query`: Original user request
   - `user_intent`: Classified intent (from intent classifier)
   - `user_specifics`: Collected user information (optional)

2. **Shared Document (Blackboard)**
   - `current_draft`: **The shared document all agents edit** (not separate versions)
   - `draft_versions`: History of changes (for tracking)
   - `current_version`: Current version number
   - `draft_edits`: Track edits made by each agent

3. **Agent Communication (Scratchpad)**
   - `agent_notes`: Notes left by agents for each other
     - Example: "Safety Agent flagged line 3; Drafter needs to revise"
     - Used for streaming "thinking" messages to UI

4. **Reviews**
   - `safety_review`: Structured safety review results
     - Status: `pending`/`passed`/`flagged`/`critical`
     - Concerns, recommendations, flagged lines
   - `clinical_review`: Structured clinical review results
     - Status: `pending`/`approved`/`needs_revision`/`rejected`
     - Scores: empathy_score, tone_score, structure_score (0-10)
     - Feedback list

5. **Debate & Argumentation**
   - `agent_debate`: Internal debate transcript
   - `debate_complete`: Whether agents have finished debating

6. **Workflow Control**
   - `iteration_count`: Current iteration (prevents infinite loops)
   - `max_iterations`: Maximum iterations before halting (default: 10)
   - `is_halted`: Whether workflow is halted for human review
   - `awaiting_human_approval`: Flag for human-in-the-loop
   - `is_approved`: Whether human has approved
   - `next_action`: Supervisor's routing decision

7. **Human-in-the-Loop**
   - `human_feedback`: Feedback from human reviewer
   - `human_edited_draft`: Human-edited version of draft
   - `final_protocol`: Final approved protocol

8. **Metadata**
   - `started_at`, `last_updated`: Timestamps
   - `current_agent`: Currently active agent

**State Hygiene:**
- All fields are typed (TypedDict) for type safety
- State is immutable in practice (agents return updated state, not modify in-place)
- Complete audit trail through `draft_versions` and `agent_notes`
- State snapshots stored in checkpoints for full history

---

## 💾 Checkpointing & Persistence

### Checkpointing Strategy

**Every node execution is checkpointed to the database.** This enables:

1. **Resume Capability**: If server crashes, workflow resumes exactly where it left off
2. **Human-in-the-Loop**: Workflow halts → state checkpointed → human reviews → state updated → workflow resumes
3. **History Logging**: All queries and generated protocols stored in database

### Checkpointer Implementation

**Location**: `backend/database.py`

**Fallback Chain** (in order of preference):

1. **AsyncSqlAlchemySaver** (PREFERRED)
   - Works with both SQLite and PostgreSQL
   - Uses SQLAlchemy async engine
   - Persistent storage

2. **AsyncPostgresSaver** (PostgreSQL-specific)
   - PostgreSQL-optimized checkpointer
   - Used if AsyncSqlAlchemySaver fails and database is PostgreSQL

3. **MemorySaver** (FALLBACK ONLY)
   - In-memory storage (NO PERSISTENCE)
   - Only used if all persistent options fail
   - **Not suitable for production** (state lost on restart)

**Checkpointing Flow:**

```
Agent Node Executes
    │
    ├─→ State Updated
    │
    ├─→ LangGraph Checkpointer Saves State
    │
    ├─→ State Serialized to Database
    │
    └─→ Checkpoint Includes:
        • Complete FoundryState
        • All agent notes
        • All reviews
        • All draft versions
        • Workflow metadata
```

### Database Tables

1. **LangGraph Checkpoints** (Managed by LangGraph)
   - Automatically created by checkpointer
   - Stores workflow state after each node execution
   - Key: `thread_id` (unique identifier for each workflow)

2. **Multi-Agent System**
 (Custom table: `protocol_history`)
   - Stores all queries and final protocols
   - Tracks status, timestamps, state snapshots
   - Fields:
     - `id` (thread_id)
     - `user_query`, `user_intent`, `user_specifics`
     - `final_protocol`
     - `state_snapshot` (full state at completion)
     - `status` (created, running, halted, approved, completed, error)
     - `started_at`, `completed_at`, `approved_at`

### Human-in-the-Loop Checkpointing Flow

```
1. Workflow halts → State checkpointed to database
2. UI fetches state from checkpoint → GET /api/protocols/{thread_id}/state
3. Human reviews draft in React UI
4. Human edits/approves → POST /api/protocols/{thread_id}/approve
5. State updated in checkpoint → graph.aupdate_state(config, updated_state)
6. Workflow resumes → Loads updated state from checkpoint and continues
```

**Key API Endpoints:**
- `GET /api/protocols/{thread_id}/state`: Gets state from checkpoint
- `POST /api/protocols/{thread_id}/approve`: Updates checkpoint with human input and resumes

---

## 🛡️ Fallbacks & Error Handling

### 1. Database Checkpointer Fallbacks

**Location**: `backend/database.py` - `get_checkpointer()`

**Fallback Chain:**
1. Try `AsyncSqlAlchemySaver` (works with SQLite and PostgreSQL)
2. Try alternative import path for `AsyncSqlAlchemySaver`
3. If PostgreSQL, try `AsyncPostgresSaver` (PostgreSQL-specific)
4. Try alternative import path for `AsyncPostgresSaver`
5. **Last Resort**: `MemorySaver` (in-memory, no persistence)

**Logging**: Comprehensive logging at each step to track which checkpointer is used

### 2. Supervisor Routing Fallbacks

**Location**: `backend/agents/supervisor.py`

**Fallback Logic:**
- If LLM returns invalid decision (not in valid_decisions list):
  - Uses strict workflow sequence based on state:
    1. No draft → `draftsman`
    2. No safety review → `safety_guardian`
    3. Safety issues → `draftsman`
    4. No clinical review → `clinical_critic`
    5. Clinical issues → `draftsman`
    6. Debate incomplete → `debate_moderator`
    7. Otherwise → `halt`

### 3. Loop Detection & Prevention

**Location**: `backend/agents/supervisor.py`

**Mechanism:**
- After 5 iterations, checks for repeated decisions
- If same decision repeated 3+ times in last 10 supervisor notes → **Halt for human review**
- Prevents infinite loops

**Max Iteration Protection:**
- Default: 10 iterations
- If `iteration_count >= max_iterations` → **Halt for human review**

### 4. Intent Classification Fallbacks

**Location**: `backend/intent_classifier.py` and `backend/main.py`

**Fallback Logic:**
- If intent classification fails → Uses `user_query` as `user_intent`
- If intent is `question` or `conversation` → Handles directly with LLM (bypasses workflow)
- If intent is `cbt_protocol` → Continues with full workflow

### 5. History Logging Fallbacks

**Location**: `backend/main.py` and `backend/history.py`

**Mechanism:**
- History module wrapped in try-except
- If history logging fails → **Warning logged, workflow continues**
- History is non-blocking (doesn't stop workflow if it fails)

### 6. Stream Error Handling

**Location**: `backend/main.py` - `stream_protocol()`

**Error Handling:**
- Try-except around entire event generator
- Errors streamed as `error` events to frontend
- Workflow status updated to `error` in `active_workflows`
- Comprehensive error logging with traceback

### 7. Graph Creation Fallbacks

**Location**: `backend/main.py` - `stream_protocol()`

**Error Handling:**
- If graph creation fails → Error event streamed to frontend
- Workflow marked as error
- Detailed error logging

### 8. State Retrieval Fallbacks

**Location**: `backend/main.py` - `get_protocol_state()`

**Error Handling:**
- If checkpoint not found → HTTP 404
- If checkpointer error → HTTP 500 with error detail
- Graceful error handling

---

## 👤 Human-in-the-Loop Integration

### Workflow Halt Mechanism

**When Workflow Halts:**
1. Supervisor decides to halt (all reviews complete, or max iterations)
2. `halt` node sets `is_halted = True`, `awaiting_human_approval = True`
3. State checkpointed to database
4. SSE stream sends `halted` event to frontend
5. Frontend shows approval section with draft

### Human Review Flow

1. **State Retrieval**: Frontend calls `GET /api/protocols/{thread_id}/state`
   - Gets current state from checkpoint
   - Displays draft in editable textarea

2. **Human Edits/Approves**: Frontend calls `POST /api/protocols/{thread_id}/approve`
   - Sends `edited_draft` (optional) and `feedback` (optional)
   - Backend:
     - Gets state from checkpoint
     - Updates state with human input:
       - `is_halted = False`
       - `awaiting_human_approval = False`
       - `is_approved = True`
       - `human_edited_draft = request.edited_draft`
       - `human_feedback = request.feedback`
       - `final_protocol = request.edited_draft or current_draft`
     - Updates checkpoint with new state
     - Logs to history
     - Returns final state

3. **Workflow Completion**: Since `is_approved = True`, workflow is complete

### Real-Time Streaming

**Server-Sent Events (SSE)**:
- `GET /api/protocols/{thread_id}/stream` streams events in real-time
- Event types:
  - `thinking`: Agent thinking/reasoning (streamed character by character)
  - `state_update`: State updates after each node
  - `halted`: Workflow halted for human review
  - `completed`: Workflow completed
  - `error`: Error occurred

**Streaming Implementation:**
- Character-by-character streaming for smooth UI effect
- Small delays (`asyncio.sleep(0.01-0.02)`) for readability
- Comprehensive error handling in stream

---

## 🔌 MCP (Model Context Protocol) Integration

### Purpose

Exposes the workflow as a tool for machine-to-machine communication (e.g., Claude Desktop).

### Implementation

**Location**: `mcp_server/mcp_server.py` and `backend/mcp_server.py`

**MCP Tool**: `create_cbt_protocol`
- **Input**: `user_query` (required), `user_specifics` (optional), `max_iterations` (optional)
- **Output**: Complete CBT protocol with full state information

**Key Features:**
- Uses same LangGraph workflow as React UI
- Autonomous execution (all agents run automatically)
- Direct protocol return (bypasses UI)
- Comprehensive error handling

**Configuration**:
- Claude Desktop config file: `claude_desktop_config.json`
- Points to MCP server Python script
- Environment variables: `OPENAI_API_KEY`, `DATABASE_URL`

---

## 🎯 Key Technical Decisions & Rationale

### 1. Why Supervisor-Worker Pattern?

**Problem**: CBT exercise design requires dynamic routing and self-correction. Unlike a linear chain, the system needs to loop back for revisions when safety or quality issues are identified.

**Solution**: Supervisor-Worker pattern with:
- Central orchestrator (Supervisor) that analyzes state
- Specialized workers (Draftsman, Safety Guardian, Clinical Critic, Debate Moderator)
- All workers return to Supervisor after tasks
- Supervisor routes dynamically based on state

**Benefits**:
- Enables iterative refinement
- Prevents infinite loops (Supervisor tracks iterations)
- Flexible routing based on workflow needs
- Self-correction capability

### 2. Why Blackboard Pattern for State?

**Problem**: Agents need to collaborate on a shared document and communicate with each other.

**Solution**: Blackboard pattern with `FoundryState`:
- `current_draft`: Shared document all agents edit
- `agent_notes`: Scratchpad for agent communication
- `draft_versions`: Complete history of changes

**Benefits**:
- Agents can see each other's work
- Complete audit trail
- Version tracking
- Effective collaboration

### 3. Why Checkpoint Every Node?

**Problem**: Need to support human-in-the-loop and resume capability.

**Solution**: Checkpoint after every node execution using LangGraph's built-in checkpointer.

**Benefits**:
- Can resume from any point if server crashes
- Human can review and edit at any point
- Complete history of workflow execution
- Zero data loss

### 4. Why Multiple Checkpointer Fallbacks?

**Problem**: Different deployment environments (PostgreSQL in production, SQLite in dev).

**Solution**: Fallback chain:
1. AsyncSqlAlchemySaver (works with both)
2. AsyncPostgresSaver (PostgreSQL-specific)
3. MemorySaver (last resort)

**Benefits**:
- Works in all environments
- Graceful degradation
- Comprehensive logging to track which checkpointer is used

### 5. Why Intent Classification?

**Problem**: Not all user queries are requests to create CBT protocols (could be questions or conversation).

**Solution**: Intent classifier routes to appropriate handler:
- `cbt_protocol` → Full workflow
- `question` → Direct LLM response
- `conversation` → Direct LLM response

**Benefits**:
- Better user experience
- Efficient resource usage
- Appropriate handling for different intents

### 6. Why SSE for Streaming?

**Problem**: Need real-time updates as agents work.

**Solution**: Server-Sent Events (SSE) for one-way streaming from server to client.

**Benefits**:
- Real-time updates
- Simple implementation
- Works well with React
- Character-by-character streaming for smooth UI

---

## 📈 Production Readiness Features

1. **Error Handling**: Comprehensive try-except blocks with logging
2. **Fallbacks**: Multiple fallback mechanisms at every critical point
3. **Logging**: Structured logging throughout the system
4. **Type Safety**: TypeScript in frontend, type hints in Python
5. **Database Health**: PostgreSQL with health checks in Docker
6. **Docker Compose**: Full containerization with proper dependencies
7. **Environment Variables**: Configurable via `.env` files
8. **Non-Blocking Operations**: History logging doesn't block workflow
9. **Graceful Degradation**: System continues even if non-critical components fail
10. **Comprehensive Documentation**: README, architecture diagrams, code comments

---

## 🔍 Where Checkpoints Are Stored

### Checkpoint Storage

1. **Database**: PostgreSQL (production) or SQLite (development)
   - Table: Managed by LangGraph checkpointer (auto-created)
   - Key: `thread_id` (unique identifier)
   - Contains: Complete `FoundryState` serialized

2. **Checkpoint Retrieval**:
   - `GET /api/protocols/{thread_id}/state`: Gets state from checkpoint
   - `graph.aget_state(config)`: LangGraph method to get checkpoint state
   - `graph.aupdate_state(config, updated_state)`: Updates checkpoint state

3. **Checkpoint Lifecycle**:
   - Created: After each node execution
   - Updated: When human approves/edits
   - Retrieved: When resuming workflow or getting state
   - Persisted: In database (PostgreSQL/SQLite)

### Checkpoint Contents

Each checkpoint contains:
- Complete `FoundryState` object
- All agent notes
- All reviews (safety, clinical)
- All draft versions
- Workflow metadata (iteration_count, timestamps, etc.)
- Human input (if any)

---

## 🚀 Deployment Architecture

### Docker Compose Setup

**Services:**
1. **postgres**: PostgreSQL 15 database
   - Port: 8008
   - Health checks enabled
   - Persistent volume

2. **backend**: FastAPI application
   - Port: 8009
   - Depends on postgres (waits for health check)
   - Auto-reload enabled in dev mode

3. **frontend**: React application
   - Port: 8010
   - Depends on backend
   - Hot reload enabled

**Networks**: All services on `mcp-chatbot-network` bridge network

**Volumes**: Persistent storage for postgres data and backend data

---

## 📝 Summary

### Key Points to Emphasize

1. **Multi-Agent Architecture**: Not a simple chain - sophisticated Supervisor-Worker pattern with dynamic routing and self-correction

2. **State Management**: Blackboard pattern with rich shared state - agents collaborate through shared document and scratchpad

3. **Checkpointing**: Every node execution checkpointed - enables resume capability and human-in-the-loop

4. **Fallbacks**: Multiple fallback mechanisms at every critical point (checkpointer, routing, intent classification, error handling)

5. **Production Ready**: Comprehensive error handling, logging, type safety, Docker deployment

6. **Human-in-the-Loop**: Seamless integration - workflow halts, state checkpointed, human reviews/edits, workflow resumes

7. **MCP Integration**: Machine-to-machine communication via Model Context Protocol

8. **Real-Time Streaming**: SSE for real-time updates as agents work

9. **Intent Classification**: Routes to appropriate handler (workflow vs. direct LLM response)

10. **Loop Prevention**: Built-in loop detection and max iteration protection

### Technical Highlights

- **LangGraph**: Workflow orchestration with built-in checkpointing
- **FastAPI**: Modern async Python web framework
- **PostgreSQL**: Production database with SQLite fallback
- **React + TypeScript**: Type-safe frontend
- **Docker Compose**: Full containerization
- **SSE**: Real-time streaming
- **MCP**: Machine-to-machine protocol

---

## 🎓 Interview Talking Points

### Architecture Decisions

**Q: Why did you choose Supervisor-Worker pattern?**
A: CBT exercise design requires dynamic routing and self-correction. Unlike a linear chain, we need to loop back for revisions when safety or quality issues are found. The Supervisor analyzes state and routes intelligently, enabling iterative refinement.

**Q: How do you prevent infinite loops?**
A: Multiple mechanisms:
1. Max iteration limit (default: 10)
2. Loop detection: After 5 iterations, if same decision repeated 3+ times → halt for human review
3. Supervisor tracks iteration_count and recent decisions

**Q: How does checkpointing work?**
A: Every node execution is checkpointed to database (PostgreSQL/SQLite). Uses LangGraph's built-in checkpointer with fallback chain: AsyncSqlAlchemySaver → AsyncPostgresSaver → MemorySaver. Enables resume capability and human-in-the-loop.

**Q: What happens if the server crashes?**
A: Workflow resumes exactly where it left off. State is checkpointed after each node, so we can resume from any checkpoint using thread_id.

**Q: How does human-in-the-loop work?**
A: Workflow halts → state checkpointed → UI fetches state → human reviews/edits → state updated in checkpoint → workflow resumes. All state changes are persisted.

**Q: What fallbacks are in place?**
A: Multiple fallbacks:
1. Checkpointer: AsyncSqlAlchemySaver → AsyncPostgresSaver → MemorySaver
2. Supervisor routing: If LLM returns invalid decision, uses strict workflow sequence
3. Intent classification: If fails, uses user_query as user_intent
4. History logging: Non-blocking, workflow continues if it fails
5. Error handling: Comprehensive try-except with logging

**Q: How do agents communicate?**
A: Through the Blackboard pattern:
- `current_draft`: Shared document all agents edit
- `agent_notes`: Scratchpad for agent communication (e.g., "Safety Agent flagged line 3")
- All agents read from and write to same state

**Q: What makes this production-ready?**
A: Comprehensive error handling, fallbacks, logging, type safety, Docker deployment, health checks, graceful degradation, non-blocking operations, and complete documentation.

---

Good luck with your interview! 🚀

