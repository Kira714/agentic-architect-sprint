# Interview Quick Reference - Personal MCP Chatbot

## 🎯 Elevator Pitch (30 seconds)

"Personal MCP Chatbot is a production-ready, autonomous multi-agent system that designs protocols through a Supervisor-Worker architecture. It uses LangGraph for workflow orchestration, checkpoints every node execution to PostgreSQL, and includes comprehensive fallbacks and human-in-the-loop integration."

---

## 🏗️ Architecture at a Glance

```
React UI / MCP Server
    ↓
FastAPI (REST + SSE)
    ↓
LangGraph Workflow (Supervisor-Worker)
    ↓
Blackboard State (FoundryState)
    ↓
PostgreSQL Checkpointer
```

---

## 🤖 Agents (5 total)

1. **Supervisor**: Routes workflow, detects loops, enforces max iterations
2. **Draftsman**: Creates/edits CBT exercises (shared document)
3. **Safety Guardian**: Reviews for safety risks (zero tolerance)
4. **Clinical Critic**: Evaluates quality (empathy, tone, structure scores)
5. **Debate Moderator**: Facilitates internal debate for refinement

**Flow**: Supervisor → Worker → Supervisor (iterative)

---

## 💾 Checkpointing

- **When**: After EVERY node execution
- **Where**: PostgreSQL (production) / SQLite (dev)
- **What**: Complete FoundryState (all agent notes, reviews, drafts)
- **Why**: Resume capability + Human-in-the-loop
- **How**: LangGraph AsyncSqlAlchemySaver (with fallbacks)

**Fallback Chain**: AsyncSqlAlchemySaver → AsyncPostgresSaver → MemorySaver

---

## 🛡️ Fallbacks

1. **Checkpointer**: 3-tier fallback (SQLAlchemy → Postgres → Memory)
2. **Supervisor Routing**: If invalid decision → strict workflow sequence
3. **Loop Detection**: After 5 iterations, if same decision 3x → halt
4. **Max Iterations**: Default 10 → halt for human review
5. **Intent Classification**: If fails → use user_query as intent
6. **History Logging**: Non-blocking (workflow continues if fails)
7. **Error Handling**: Try-except with logging at every critical point

---

## 📊 State Management (Blackboard Pattern)

**Key Fields**:
- `current_draft`: Shared document (all agents edit this)
- `agent_notes`: Scratchpad for agent communication
- `safety_review`: Safety review results (status, concerns, recommendations)
- `clinical_review`: Clinical review results (scores, feedback)
- `iteration_count`: Prevents infinite loops
- `is_halted`: Human-in-the-loop flag
- `next_action`: Supervisor's routing decision

**Pattern**: All agents read/write to same state (Blackboard)

---

## 🔌 MCP (Model Context Protocol) Integration

**Purpose**: Machine-to-machine communication - exposes workflow as a tool for AI assistants (e.g., Claude Desktop)

**Implementation**:
- **File**: `mcp_server/mcp_server.py`
- **Tool Name**: `create_protocol`
- **Protocol**: Model Context Protocol (MCP) standard

**How It Works**:
1. MCP server exposes `create_protocol` tool
2. AI assistant (Claude Desktop) calls the tool with user query
3. MCP server executes full LangGraph workflow autonomously
4. All agents run automatically (Supervisor, Draftsman, Safety, Clinical, Debate)
5. Auto-approves if workflow halts (no human-in-the-loop for MCP)
6. Returns final protocol directly to AI assistant

**Key Features**:
- **Same Backend Logic**: Uses exact same LangGraph workflow as React UI
- **Autonomous Execution**: Runs all agents without human intervention
- **Direct Return**: Returns protocol directly (bypasses UI)
- **Auto-Approval**: If workflow halts, auto-approves and continues
- **Complete State**: Returns protocol with full metadata (iterations, reviews, etc.)

**Tool Parameters**:
- `user_query` (required): User's request for CBT exercise
- `user_intent` (optional): Pre-classified intent
- `max_iterations` (optional, default: 10): Max iterations before halting

**Configuration**:
- Claude Desktop config: `claude_desktop_config.json`
- Points to MCP server Python script
- Environment variables: `OPENAI_API_KEY`, `DATABASE_URL`

**Use Case**: Allows AI assistants to create CBT protocols programmatically without UI interaction

---

## 👤 Human-in-the-Loop Flow

1. Workflow halts → State checkpointed
2. UI fetches state → `GET /api/protocols/{thread_id}/state`
3. Human reviews/edits draft
4. Human approves → `POST /api/protocols/{thread_id}/approve`
5. State updated in checkpoint
6. Workflow resumes (or completes if approved)

---

## 🔌 Key Technologies

- **LangGraph**: Workflow orchestration + checkpointing
- **FastAPI**: REST API + SSE streaming
- **PostgreSQL**: Database (with SQLite fallback)
- **React + TypeScript**: Frontend
- **MCP**: Machine-to-machine protocol

---

## 🎯 Key Technical Decisions

1. **Supervisor-Worker**: Enables dynamic routing + self-correction
2. **Blackboard State**: Agents collaborate through shared document
3. **Checkpoint Every Node**: Resume capability + human-in-the-loop
4. **Multiple Fallbacks**: Graceful degradation at every level
5. **SSE Streaming**: Real-time updates as agents work
6. **Intent Classification**: Routes to appropriate handler

---

## 📝 Common Interview Questions

**Q: Why Supervisor-Worker?**
A: Need dynamic routing and self-correction. Supervisor analyzes state and routes intelligently, enabling iterative refinement when issues are found.

**Q: How prevent infinite loops?**
A: Max iterations (10), loop detection (same decision 3x after 5 iterations → halt), Supervisor tracks iteration_count.

**Q: How does checkpointing work?**
A: Every node execution checkpointed to PostgreSQL. LangGraph checkpointer with fallback chain. Enables resume and human-in-the-loop.

**Q: What if server crashes?**
A: Resume from last checkpoint using thread_id. State persisted after every node.

**Q: How do agents communicate?**
A: Blackboard pattern - shared `current_draft` and `agent_notes` scratchpad.

**Q: What fallbacks exist?**
A: Checkpointer (3-tier), routing (strict sequence), loop detection, max iterations, intent classification, error handling.

**Q: What is MCP integration?**
A: Model Context Protocol (MCP) exposes the workflow as a tool for AI assistants (e.g., Claude Desktop). Uses same LangGraph workflow as React UI, runs autonomously, auto-approves if halted, returns protocol directly. Enables machine-to-machine communication without UI.

---

## 🚀 Production Readiness

✅ Error handling (try-except everywhere)
✅ Fallbacks (multiple layers)
✅ Logging (structured)
✅ Type safety (TypeScript + type hints)
✅ Docker deployment
✅ Health checks
✅ Graceful degradation
✅ Non-blocking operations

---

## 📍 File Locations

- **Graph**: `backend/graph.py`
- **State**: `backend/state.py`
- **Checkpointer**: `backend/database.py`
- **Supervisor**: `backend/agents/supervisor.py`
- **API**: `backend/main.py`
- **MCP**: `mcp_server/mcp_server.py`

---

## 💡 Key Numbers

- **Agents**: 5 (Supervisor + 4 workers)
- **Max Iterations**: 10 (default)
- **Loop Detection**: After 5 iterations, 3x same decision
- **Checkpoint Frequency**: Every node execution
- **Fallback Levels**: 3 (checkpointer), multiple (routing, errors)

---

Good luck! 🎯


