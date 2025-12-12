# Cerina Protocol Foundry

> **An Intelligent Multi-Agent System for Autonomous CBT Exercise Design**

The Cerina Protocol Foundry is a production-ready, autonomous multi-agent system that acts as a **clinical foundry**—intelligently designing, critiquing, and refining Cognitive Behavioral Therapy (CBT) exercises through rigorous internal debate and self-correction before presenting results to humans. This system demonstrates advanced agentic architecture, deep state management, persistent checkpointing, and seamless human-in-the-loop integration.

## 📋 Deliverables

### 1. Code Repository
- **Modular Architecture**: Clean separation of concerns with dedicated modules for agents, state management, persistence, and interfaces
- **Well-Documented**: Comprehensive docstrings, type hints, and inline comments throughout the codebase
- **Production-Ready**: Error handling, logging, and robust error recovery mechanisms
- **Repository**: [GitHub Repository](https://github.com/Kira714/agentic-architect-sprint)

### 2. Architecture Diagram

**Architecture Diagram URL**: [MERMAID_ARCHITECTURE_DIAGRAM.md](./MERMAID_ARCHITECTURE_DIAGRAM.md)

The system architecture is visualized in multiple formats:

- **Mermaid Diagrams** (Primary): [MERMAID_ARCHITECTURE_DIAGRAM.md](./MERMAID_ARCHITECTURE_DIAGRAM.md) contains interactive Mermaid diagrams showing:
  - **Agent Topology**: Supervisor-Worker pattern with all agents (Supervisor, Draftsman, Safety Guardian, Clinical Critic, Debate Moderator)
  - **Full System Architecture**: All layers from UI to persistence
  - **Data Flow**: Sequence diagram showing workflow execution
  - **State Structure**: Blackboard pattern with FoundryState schema

- **ASCII Diagram**: See the "High-Level Architecture" section below for a text-based visualization

**Note**: The `context_analyzer` agent exists in the codebase but is not part of the active workflow. The architecture diagram shows only the agents that are actively used in the LangGraph workflow.

The architecture includes:
- User interface layer (React Dashboard + MCP Server)
- API layer (FastAPI with REST endpoints)
- LangGraph workflow (Supervisor-Worker pattern)
- State management (Blackboard pattern)
- Persistence layer (PostgreSQL/SQLite with checkpointing)

### 3. Loom Video (5 minutes)
The demo video covers:
- **React UI Demo**: Real-time agent activity, debate/refinement process, human-in-the-loop interruption, and final approval workflow
- **MCP Demo**: Connection to Claude Desktop, triggering workflow remotely via MCP tool, and receiving protocol directly
- **Code Walkthrough**: Brief explanation of `FoundryState` definition (Blackboard pattern) and checkpointer logic (persistent state management)

### 4. Evaluation Criteria
All evaluation criteria are comprehensively met and documented in the "Evaluation Criteria" section below, with detailed explanations of how each criterion is satisfied.

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  React Dashboard (UI)          │ MCP Server (Machine-to-Machine)│
│  - Real-time streaming         │  - Tool: create_cbt_protocol   │
│  - Human-in-the-loop           │  - Returns protocol directly   │
│  - State visualization         │  - Uses same backend logic     │
└──────────────┬─────────────────┴──────────────────┬─────────────┘
               │                                    │
               └──────────────┬─────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                    API LAYER (FastAPI)                        │
│  - /api/protocols/create  (creates thread, returns thread_id) │
│  - /api/protocols/{id}/stream  (SSE streaming)                │
│  - /api/protocols/{id}/approve  (resumes from checkpoint)     │
│  - /api/protocols/{id}/state  (gets state from checkpoint)    │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              LANGGRAPH WORKFLOW (Supervisor-Worker)           │
│                                                               │
│  ┌──────────────┐                                             │
│  │  SUPERVISOR  │  ← Entry Point                              │
│  │ (Orchestrator)│                                            │
│  └──────┬───────┘                                             │
│         │                                                     │
│    ┌────┴─────┬──────────┬─────────┬─────────┐                │
│    │          │          │         │         │                │
│  ┌─▼───┐  ┌───▼──┐  ┌────▼───┐ ┌───▼─────┐   │                │
│  │Draft│  │Safety│  │Clinical│ │Debate   │   │                │
│  │sman │  │Guard │  │Critic  │ │Moderator│   │                │
│  └───┬─┘  └───┬──┘  └────┬───┘ └───┬─────┘   │                │
│      │        │          │         │         │                │
│      └────────┴──────────┴─────────┴─────────┘                │
│                    All return to Supervisor                   │
│                                                               │
│  ┌──────────┐  ┌──────────┐                                   │
│  │   HALT   │  │  APPROVE │  ← Terminal nodes                 │
│  │ (Human)  │  │(Finalize)│                                   │
│  └──────────┘  └──────────┘                                   │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              STATE MANAGEMENT (Blackboard Pattern)            │
│                                                               │
│  FoundryState (Shared State):                                 │
│  - user_query, user_intent, user_specifics                    │
│  - current_draft (shared document)                            │
│  - draft_versions, draft_edits                                │
│  - agent_notes (scratchpad for communication)                 │
│  - safety_review, clinical_review                             │
│  - agent_debate (internal debate transcript)                  │
│  - is_halted, awaiting_human_approval                         │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              PERSISTENCE LAYER                                │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  LangGraph Checkpointer (PostgreSQL/SQLite)          │     │
│  │  - Every node execution is checkpointed              │     │
│  │  - Can resume from any checkpoint                    │     │
│  │  - Human-in-the-loop uses checkpoint state           │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  Protocol History Table                              │     │
│  │  - Stores all queries and final protocols            │     │
│  │  - Tracks status, timestamps, state snapshots        │     │
│  └──────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

### Agent Architecture (Supervisor-Worker Pattern)

The system uses a **Supervisor-Worker pattern** with specialized agents that collaborate through a shared state (Blackboard pattern). This is NOT a trivial linear chain—it's a robust, self-correcting system with autonomous agents that debate, refine, and self-correct.

#### 1. **Supervisor Agent** (Orchestrator)
- **Role**: Central orchestrator and routing decision-maker
- **Responsibilities**:
  - Analyzes complete workflow state with maximum precision
  - Makes evidence-based routing decisions
  - Detects infinite loops and self-corrects
  - Decides when to halt for human review
  - Ensures strict adherence to workflow sequence
- **System Prompt**: Maximum precision, context-awareness, strict compliance
- **Routing Logic**: Follows mandatory workflow protocol with zero tolerance for deviations

#### 2. **Draftsman Agent** (Exercise Creator)
- **Role**: Creates and revises CBT exercise drafts
- **Responsibilities**:
  - Creates evidence-based, professional CBT exercises
  - Edits shared document (Blackboard pattern)
  - Incorporates feedback from reviews and debate
  - Ensures exercises surpass medical standards
  - Includes all required clinical components (SUDS, progression criteria, safety behaviors, etc.)
- **System Prompt**: Expert-level CBT knowledge, clinical rigor, evidence-based protocols
- **Output**: Practice-ready CBT exercises with proper markdown formatting

#### 3. **Safety Guardian Agent** (Safety Reviewer)
- **Role**: Comprehensive safety review with zero tolerance
- **Responsibilities**:
  - Reviews for self-harm risks and triggers
  - Checks for medical advice exceeding therapeutic boundaries
  - Identifies dangerous or harmful instructions
  - Ensures safety disclaimers and crisis resources
  - Verifies contraindications and red flags
- **System Prompt**: Zero tolerance for safety risks, comprehensive analysis
- **Output**: Safety review with status (passed/flagged/critical), concerns, and recommendations

#### 4. **Clinical Critic Agent** (Quality Evaluator)
- **Role**: Rigorous clinical quality evaluation
- **Responsibilities**:
  - Evaluates empathy, tone, and structure (0-10 scales)
  - Assesses therapeutic effectiveness
  - Verifies evidence-based foundation
  - Ensures clinical completeness
  - Provides specific, actionable feedback
- **System Prompt**: Rigorous evidence-based evaluation, maximum stringency
- **Output**: Clinical review with scores and feedback

#### 5. **Debate Moderator Agent** (Internal Refinement)
- **Role**: Facilitates systematic internal debate
- **Responsibilities**:
  - Orchestrates evidence-based debate between agents
  - Ensures all clinical concerns are addressed
  - Reaches consensus on refinements needed
  - Final quality check before human review
- **System Prompt**: Systematic clinical review board protocol
- **Output**: Debate transcript with consensus and refinements

### State Management (Blackboard Pattern)

The `FoundryState` is a **rich, structured shared state** (Blackboard pattern) where all agents read from and write to:

**State Definition** (`backend/state.py`):
- **User Input**: `user_query`, `user_intent`, `user_specifics`
- **Shared Document**: `current_draft` - All agents edit the same document collaboratively (not separate versions)
- **Version Control**: `draft_versions`, `draft_edits`, `current_version` - Tracks all changes with timestamps and agent attribution
- **Agent Communication**: `agent_notes` - Scratchpad where agents leave notes for each other (e.g., "Safety Agent flagged line 3; Drafter needs to revise")
- **Reviews**: `safety_review`, `clinical_review` - Structured review results with status, scores, concerns, and recommendations
- **Debate**: `agent_debate`, `debate_complete` - Internal debate transcript and consensus
- **Learning**: `learned_patterns`, `adaptation_notes` - System learning and adaptation over time
- **Workflow Control**: `is_halted`, `awaiting_human_approval`, `iteration_count`, `max_iterations`, `is_approved`
- **Metadata**: `started_at`, `last_updated`, `final_protocol`, `human_feedback`, `human_edited_draft`

**State Hygiene**:
- All state fields are typed (TypedDict) for type safety
- State is immutable in practice (agents return updated state, not modify in-place)
- Complete audit trail through `draft_versions` and `agent_notes`
- State snapshots stored in checkpoints for full history

This is NOT just a list of messages—it's a comprehensive project workspace that tracks the entire workflow from initial request to final approval, enabling effective agent collaboration through the shared blackboard.

### Persistence & Checkpointing

**Every step of the graph is checkpointed to the database**. This enables:

1. **Resume Capability**: If the server crashes, it resumes exactly where it left off
2. **Human-in-the-Loop**: Workflow halts → state checkpointed → human reviews → state updated → workflow resumes
3. **History Logging**: All queries and generated protocols are stored in the database

**Checkpointing Strategy**:
- **Every Node Execution**: State is checkpointed after each agent node execution
- **Database**: PostgreSQL (production) with SQLite fallback (development)
- **Checkpointer**: LangGraph AsyncSqlAlchemySaver or AsyncPostgresSaver
- **Resume**: Can resume from any checkpoint using `thread_id`
- **State Retrieval**: `/api/protocols/{thread_id}/state` endpoint fetches state from checkpoint

**Checkpointer Logic**:
- Uses LangGraph's built-in checkpointing system
- State is serialized and stored in database after each node
- Checkpoint includes complete `FoundryState` with all agent notes, reviews, and draft versions
- Human-in-the-loop workflow: When workflow halts, state is checkpointed → UI fetches state → Human edits/approves → State updated in checkpoint → Workflow resumes from updated checkpoint

**Database Tables**:
- **LangGraph Checkpoints**: Managed automatically by LangGraph checkpointer (stores workflow state)
- **Protocol History**: Custom table (`protocol_history`) stores all queries, final protocols, and state snapshots

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (optional, SQLite works for development)
- OpenAI API key

### Option 1: Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/Kira714/agentic-architect-sprint.git
cd agentic-architect-sprint
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Access the system:**
- Frontend Dashboard: http://localhost:8006
- Backend API: http://localhost:8005
- API Documentation: http://localhost:8005/docs
- PostgreSQL: localhost:8007

### Option 2: Local Development

1. **Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment:**
Create `backend/.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./cerina_foundry.db
OPENAI_MODEL=gpt-4o-mini
```

3. **Run Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8005
```

4. **Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

5. **Access Dashboard:**
Open http://localhost:5173 (or the port shown in terminal)

---

## 📖 Usage

### React Dashboard (Human-in-the-Loop)

1. **Create Protocol:**
   - Enter a query (e.g., "Create an exposure hierarchy for agoraphobia")
   - Click "Create Protocol"

2. **Watch Agents Work:**
   - Real-time streaming shows agent thinking and actions
   - See agents debate, refine, and self-correct
   - View state updates as they happen

3. **Human Review:**
   - Workflow halts automatically when ready
   - Review the generated draft
   - Edit if needed (optional)
   - Click "Approve & Finalize"

4. **Final Protocol:**
   - Protocol is saved to database
   - Can be viewed in history

### MCP Server (Machine-to-Machine)

The MCP server implements the **Model Context Protocol (MCP)** standard, exposing the workflow as a tool for machine-to-machine communication.

**MCP Tool**: `create_cbt_protocol`
- **Description**: Creates a CBT exercise protocol using the multi-agent system
- **Input**: `user_query` (required), `user_specifics` (optional), `max_iterations` (optional, default: 10)
- **Output**: Complete CBT protocol with full state information

**Setup (Claude Desktop):**

1. **Create MCP Configuration:**
   Create/update `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": ["C:\\full\\path\\to\\agentic-architect-sprint\\backend\\mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "DATABASE_URL": "sqlite+aiosqlite:///./cerina_foundry.db"
      }
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Use the Tool:**
   In Claude Desktop, you can now use:
   ```
   Use the cerina-foundry tool to create a sleep hygiene protocol for insomnia.
   ```

**MCP Integration Details**:
- **Same Backend Logic**: MCP server uses the exact same LangGraph workflow as the React UI
- **Autonomous Execution**: Runs all agents (Supervisor, Draftsman, Safety Guardian, Clinical Critic, Debate Moderator) autonomously
- **Direct Return**: Returns final protocol directly to MCP client (bypasses UI)
- **Error Handling**: Comprehensive error handling and logging for MCP context
- **Implementation**: Uses `mcp-python` SDK with proper tool registration and call handling

**MCP Demo Requirements**:
- Connect MCP server to Claude Desktop (or other MCP client)
- Trigger workflow remotely via MCP tool call
- Show workflow execution (agents working autonomously)
- Receive final protocol directly in MCP client

---

## 🔍 Visualizing the Graph in Action

### Method 1: Real-Time Dashboard (Recommended)

The React dashboard provides real-time visualization:

1. **Start the backend and frontend** (see Quick Start)
2. **Open the dashboard** in your browser
3. **Create a protocol** and watch:
   - Agent thinking messages (streaming)
   - State updates in real-time
   - Agent routing decisions
   - Draft versions and edits
   - Review results

### Method 2: Backend Logs

The backend logs show detailed agent activity:

```bash
# Run backend with verbose logging
cd backend
python -m uvicorn main:app --reload --log-level debug
```

You'll see:
```
[SUPERVISOR] Making routing decision (Iteration 0)
[SUPERVISOR] Decision: draftsman
[DRAFTSMAN] Starting draft work (Iteration 0)
[DRAFTSMAN] Created shared document version 1 (1234 chars)
[SAFETY GUARDIAN] Reviewing draft for safety concerns
[SAFETY GUARDIAN] Review complete: PASSED
[CLINICAL CRITIC] Reviewing draft for clinical quality
[CLINICAL CRITIC] Review complete: approved (Avg: 8.5/10)
[DEBATE MODERATOR] Facilitating internal debate on draft quality
[HALT] Execution halted for human review - state checkpointed to database
```

### Method 3: Database Inspection

Check the database to see checkpointed state:

```python
# Python script to inspect checkpoints
from database import get_checkpointer
import asyncio

async def inspect_checkpoint(thread_id):
    checkpointer = await get_checkpointer()
    # Get checkpoint state
    # (Implementation depends on checkpointer type)
```

### Method 4: API Endpoints

Query the API to see current state:

```bash
# Get current state
curl http://localhost:8005/api/protocols/{thread_id}/state

# Stream events
curl http://localhost:8005/api/protocols/{thread_id}/stream
```

### Method 5: LangGraph Visualization (Advanced)

You can visualize the graph structure programmatically:

```python
from graph import create_foundry_graph
import asyncio

async def visualize_graph():
    graph = await create_foundry_graph()
    # Print graph structure
    print(graph.get_graph().draw_mermaid())
```

---

## 🎬 Demo Scenarios

### Scenario 1: Basic Protocol Creation

1. **Query**: "Create an exposure hierarchy for agoraphobia"
2. **Workflow**:
   - Supervisor → Draftsman (creates initial draft)
   - Supervisor → Safety Guardian (safety review)
   - Supervisor → Clinical Critic (clinical review)
   - Supervisor → Debate Moderator (internal debate)
   - Supervisor → Halt (human review)
3. **Human**: Reviews draft, approves
4. **Result**: Final protocol saved to database

### Scenario 2: Iterative Refinement

1. **Query**: "Create a thought record exercise for anxiety"
2. **Workflow**:
   - Draftsman creates draft
   - Safety Guardian flags a concern
   - Supervisor routes back to Draftsman
   - Draftsman revises based on feedback
   - Process repeats until all reviews pass
3. **Result**: Refined protocol after multiple iterations

### Scenario 3: MCP Integration

1. **User**: Prompts Claude Desktop: "Ask Cerina Foundry to create a sleep hygiene protocol"
2. **MCP Server**: Triggers workflow
3. **Workflow**: Runs autonomously (all agents)
4. **Result**: Protocol returned directly to Claude Desktop

---

## 🔧 Technology Stack

### Backend
- **Python 3.10+**: Core language
- **LangGraph**: Workflow orchestration and checkpointing
- **LangChain**: LLM integration
- **FastAPI**: REST API and streaming
- **SQLAlchemy**: Database ORM
- **PostgreSQL/SQLite**: Persistent storage

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **react-markdown**: Markdown rendering
- **remark-gfm**: GitHub Flavored Markdown (tables)

### MCP
- **mcp-python SDK**: Model Context Protocol implementation

### LLM
- **OpenAI GPT-4**: Primary LLM (configurable via `OPENAI_MODEL`)

---


---

## 🏆 Evaluation Criteria

### 1. Architectural Ambition ✅

**Did you build a trivial chain, or did you design a robust, self-correcting system?**

The system implements a **Supervisor-Worker pattern** with autonomous agents, NOT a trivial linear chain. Key features:

- **Dynamic Routing**: Supervisor analyzes complete state and routes to appropriate agents based on workflow needs
- **Self-Correction**: Built-in loop detection prevents infinite cycles; agents can route back for revisions when issues are found
- **Complex Reasoning**: Agents engage in internal debate through the Debate Moderator, refining exercises before human review
- **Autonomous Operation**: System works independently, only halting for human approval when workflow is complete
- **Iterative Refinement**: Can loop back through agents multiple times (e.g., Draftsman → Safety Guardian → Draftsman if safety issues found)

**Architecture Choice**: Supervisor-Worker pattern was chosen because CBT exercise design requires dynamic routing and self-correction. Unlike a linear chain, the system needs to loop back for revisions when safety or quality issues are identified. The Supervisor analyzes state (draft existence, review status, iteration count) and routes dynamically. All workers return to the Supervisor after completing tasks, enabling iteration and refinement. Combined with a Blackboard pattern for shared state, specialized agents (Draftsman, Safety Guardian, Clinical Critic, Debate Moderator) collaborate through a shared document (`current_draft`) and communication scratchpad (`agent_notes`) without direct agent-to-agent communication. The Supervisor also handles human-in-the-loop by halting execution when needed, with state checkpointed for seamless resumption after approval.

### 2. State Hygiene ✅

**How effectively did you use the shared state/scratchpad?**

The system implements a **Blackboard pattern** with a rich, structured shared state (`FoundryState`):

- **Shared Document**: `current_draft` - All agents collaboratively edit the same document (not separate versions)
- **Agent Communication**: `agent_notes` - Scratchpad where agents leave notes for each other (e.g., "Safety Agent flagged line 3; Drafter needs to revise")
- **Version Tracking**: `draft_versions` and `draft_edits` - Complete history of all changes with timestamps and agent attribution
- **Review Metadata**: `safety_review` and `clinical_review` - Structured review results with status, scores, concerns, and recommendations
- **Debate Transcript**: `agent_debate` - Internal debate transcript showing agent arguments and consensus
- **Workflow Metadata**: `iteration_count`, `current_version`, `is_halted`, `awaiting_human_approval` - Complete workflow state tracking
- **Learning Patterns**: `learned_patterns` and `adaptation_notes` - System learning and adaptation over time

This is NOT just a list of messages—it's a comprehensive project workspace that tracks the entire workflow from initial request to final approval, enabling effective agent collaboration.

### 3. Persistence ✅

**Does the Human-in-the-Loop flow work reliably using database checkpoints?**

Yes, the system implements **full checkpointing** with reliable human-in-the-loop integration:

- **Every Node Execution Checkpointed**: State is saved to database after each agent node execution
- **Resume Capability**: Can resume from any checkpoint using `thread_id` - if server crashes, workflow resumes exactly where it left off
- **Human-in-the-Loop Flow**:
  1. Workflow halts → State checkpointed to database
  2. Human reviews draft via React UI → Fetches state from checkpoint
  3. Human edits/approves → State updated in checkpoint
  4. Workflow resumes → Loads updated state from checkpoint and continues
- **Database Backend**: PostgreSQL (with SQLite fallback) using LangGraph's AsyncSqlAlchemySaver or AsyncPostgresSaver
- **History Logging**: All queries and final protocols stored in `protocol_history` table with full state snapshots

The checkpointing system ensures zero data loss and seamless human intervention at any point in the workflow.

### 4. MCP Integration ✅

**Did you successfully implement the new interoperability standard?**

Yes, the system includes a **complete MCP (Model Context Protocol) server** implementation:

- **Tool Exposure**: Exposes `create_cbt_protocol` tool that triggers the full LangGraph workflow
- **Machine-to-Machine Communication**: Works with Claude Desktop and other MCP clients
- **Same Backend Logic**: MCP server uses the exact same LangGraph workflow as the React UI
- **Direct Protocol Return**: Returns final protocol directly to MCP client, bypassing UI (optional human-in-the-loop)
- **Implementation**: Uses `mcp-python` SDK with proper error handling and logging
- **Configuration**: Supports both local and remote MCP server setups

The MCP integration demonstrates the system's interoperability and ability to work seamlessly with other AI systems.

### 5. AI Leverage ✅

**Did you use AI coding tools to deliver a "weeks worth of work" in 5 days?**

Yes, the system was built using AI coding assistants (Cursor, Claude) to rapidly scaffold, generate, and debug code:

- **Comprehensive System**: Multi-agent architecture with 5 specialized agents, persistent checkpointing, real-time streaming, and dual interfaces (React + MCP)
- **Rapid Development**: Delivered production-ready system with complex features in 5 days
- **Complex Architecture**: Supervisor-Worker pattern, Blackboard state management, checkpointing, human-in-the-loop, MCP integration
- **Code Quality**: Despite rapid development, code is modular, well-documented, and production-ready

---

## 📚 Code Repository Structure

The codebase is **modular, clean, and well-documented**:

```
.
├── backend/                    # Python backend
│   ├── agents/                 # Agent implementations (modular)
│   │   ├── supervisor.py      # Orchestrator agent
│   │   ├── draftsman.py       # Exercise creator
│   │   ├── safety_guardian.py # Safety reviewer
│   │   ├── clinical_critic.py # Quality evaluator
│   │   └── debate_moderator.py # Debate facilitator
│   ├── state.py               # State schema (Blackboard pattern)
│   ├── graph.py               # LangGraph workflow definition
│   ├── database.py            # Checkpointing and database setup
│   ├── main.py                # FastAPI server (REST API)
│   ├── mcp_server.py          # MCP server (machine-to-machine)
│   ├── history.py             # Protocol history logging
│   ├── intent_classifier.py   # Intent classification
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ChatMessage.tsx
│   │   │   └── Icons.tsx
│   │   ├── App.tsx            # Main application component
│   │   ├── api.ts             # API client
│   │   └── types.ts           # TypeScript type definitions
│   └── package.json           # Node dependencies
├── docker-compose.yml         # Docker orchestration
├── .env.example              # Environment variable template
└── README.md                 # This file
```

**Code Quality Features**:
- **Type Safety**: Full TypeScript in frontend, type hints in Python backend
- **Error Handling**: Comprehensive try-catch blocks with proper error messages
- **Logging**: Structured logging throughout the system
- **Documentation**: Docstrings for all functions and classes
- **Modularity**: Clear separation of concerns (agents, state, persistence, interfaces)

---

## 🔐 Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
OPENAI_MODEL=gpt-4o-mini
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError`  
**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: Database connection errors  
**Solution**: Check `DATABASE_URL` in `.env` file. For SQLite, use: `sqlite+aiosqlite:///./cerina_foundry.db`

**Problem**: Checkpointer errors  
**Solution**: Ensure database tables are created. The checkpointer will create them automatically on first run.

### Frontend Issues

**Problem**: `Failed to resolve import`  
**Solution**: Install dependencies:
```bash
cd frontend
npm install
```

**Problem**: CORS errors  
**Solution**: Check `CORS_ORIGINS` in backend `main.py` includes your frontend URL.

### MCP Issues

**Problem**: "Server disconnected" in Claude Desktop  
**Solution**: 
- Check Python path in MCP config
- Ensure `mcp` package is installed: `pip install mcp`
- Check environment variables are set correctly
- See [LOCAL_MCP_SETUP.md](./LOCAL_MCP_SETUP.md) for detailed troubleshooting

---

## 📝 License

This project is built for the Cerina Protocol Foundry challenge.

---

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) for LLM integration
- [FastAPI](https://fastapi.tiangolo.com/) for the API
- [Model Context Protocol](https://modelcontextprotocol.io/) for interoperability

---

## 📧 Contact

For questions or issues, please open an issue on GitHub: https://github.com/Kira714/agentic-architect-sprint
