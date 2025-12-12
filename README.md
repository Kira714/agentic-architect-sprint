# Cerina Protocol Foundry

> **An Intelligent Multi-Agent System for Autonomous CBT Exercise Design**

The Cerina Protocol Foundry is a sophisticated, autonomous multi-agent system that acts as a **clinical foundry**—intelligently designing, critiquing, and refining Cognitive Behavioral Therapy (CBT) exercises through rigorous internal debate and self-correction before presenting results to humans. This system demonstrates advanced agentic architecture, deep state management, persistent checkpointing, and seamless human-in-the-loop integration.

---

## 🎯 Mission Statement

At Cerina, we don't just build chatbots; we build **autonomous systems that act as clinical foundries**. This system autonomously designs, critiques, and refines CBT exercises using a rigorous multi-agent architecture that mimics a clinical review board. The system demonstrates:

- **Autonomous Multi-Agent Collaboration**: Specialized agents that debate, refine, and self-correct
- **Deep State Management**: Rich shared state (Blackboard pattern) for inter-agent communication
- **Persistent Checkpointing**: Full workflow state persistence with resume capability
- **Human-in-the-Loop**: Seamless interruption and resumption for human review
- **MCP Integration**: Machine-to-machine interoperability via Model Context Protocol

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  React Dashboard (UI)          │  MCP Server (Machine-to-Machine)│
│  - Real-time streaming         │  - Tool: create_cbt_protocol    │
│  - Human-in-the-loop           │  - Returns protocol directly    │
│  - State visualization         │  - Uses same backend logic      │
└──────────────┬─────────────────┴────────────────┬────────────────┘
               │                                   │
               └──────────────┬────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                    API LAYER (FastAPI)                         │
│  - /api/protocols/create  (creates thread, returns thread_id)  │
│  - /api/protocols/{id}/stream  (SSE streaming)                │
│  - /api/protocols/{id}/approve  (resumes from checkpoint)     │
│  - /api/protocols/{id}/state  (gets state from checkpoint)     │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              LANGGRAPH WORKFLOW (Supervisor-Worker)            │
│                                                                │
│  ┌──────────────┐                                             │
│  │  SUPERVISOR  │  ← Entry Point                              │
│  │  (Orchestrator)│                                            │
│  └──────┬───────┘                                             │
│         │                                                      │
│    ┌────┴─────┬──────────┬──────────┬──────────┐            │
│    │          │          │          │          │            │
│  ┌─▼──┐  ┌───▼──┐  ┌────▼───┐ ┌───▼────┐ ┌───▼─────┐    │
│  │Draft│  │Safety│  │Clinical│ │Debate  │            │    │
│  │sman │  │Guard │  │Critic  │ │Moderator│           │    │
│  └───┬──┘  └───┬──┘  └────┬───┘ └───┬────┘           │    │
│      │         │          │         │                │    │
│      └─────────┴──────────┴─────────┴────────────────┘    │
│                    All return to Supervisor                  │
│                                                                │
│  ┌──────────┐  ┌──────────┐                                 │
│  │   HALT   │  │  APPROVE │  ← Terminal nodes                │
│  │ (Human)  │  │ (Finalize)│                                 │
│  └──────────┘  └──────────┘                                 │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              STATE MANAGEMENT (Blackboard Pattern)              │
│                                                                │
│  FoundryState (Shared State):                                  │
│  - user_query, user_intent, user_specifics                    │
│  - current_draft (shared document)                             │
│  - draft_versions, draft_edits                                │
│  - agent_notes (scratchpad for communication)                  │
│  - safety_review, clinical_review                              │
│  - agent_debate (internal debate transcript)                   │
│  - is_halted, awaiting_human_approval                         │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              PERSISTENCE LAYER                                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  LangGraph Checkpointer (PostgreSQL/SQLite)          │    │
│  │  - Every node execution is checkpointed               │    │
│  │  - Can resume from any checkpoint                    │    │
│  │  - Human-in-the-loop uses checkpoint state            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Protocol History Table                              │    │
│  │  - Stores all queries and final protocols            │    │
│  │  - Tracks status, timestamps, state snapshots        │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
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

- **Shared Document**: `current_draft` - All agents edit the same document collaboratively
- **Communication**: `agent_notes` - Agents leave notes for each other (scratchpad)
- **Version Control**: `draft_versions`, `draft_edits` - Tracks all changes and history
- **Reviews**: `safety_review`, `clinical_review` - Review results with status and feedback
- **Debate**: `agent_debate` - Internal debate transcript and consensus
- **Learning**: `learned_patterns`, `adaptation_notes` - System learning and adaptation
- **Workflow Control**: `is_halted`, `awaiting_human_approval`, `iteration_count`

This is NOT just a list of messages—it's a comprehensive project workspace that tracks the entire workflow from initial request to final approval.

### Persistence & Checkpointing

**Every step of the graph is checkpointed to the database**. This enables:

1. **Resume Capability**: If the server crashes, it resumes exactly where it left off
2. **Human-in-the-Loop**: Workflow halts → state checkpointed → human reviews → state updated → workflow resumes
3. **History Logging**: All queries and generated protocols are stored in the database

**Checkpointing Strategy**:
- **Every Node Execution**: State is checkpointed after each agent node
- **Database**: PostgreSQL (with SQLite fallback)
- **Checkpointer**: LangGraph AsyncSqlAlchemySaver or AsyncPostgresSaver
- **Resume**: Can resume from any checkpoint using `thread_id`

**Database Tables**:
- **LangGraph Checkpoints**: Managed by LangGraph checkpointer (automatic)
- **Protocol History**: Stores all queries, protocols, and state snapshots (custom table)

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

The MCP server exposes the workflow as a tool for machine-to-machine communication.

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

The MCP server will:
- Trigger the full LangGraph workflow
- Run all agents autonomously
- Return the final protocol directly
- Bypass the React UI (but uses the same backend logic)

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

## 📁 Project Structure

```
.
├── backend/                    # Python backend
│   ├── agents/                 # Agent implementations
│   │   ├── supervisor.py      # Orchestrator agent
│   │   ├── draftsman.py       # Exercise creator
│   │   ├── safety_guardian.py # Safety reviewer
│   │   ├── clinical_critic.py # Quality evaluator
│   │   └── debate_moderator.py # Debate facilitator
│   ├── state.py               # State schema (Blackboard)
│   ├── graph.py               # LangGraph workflow
│   ├── database.py            # Checkpointing setup
│   ├── main.py                # FastAPI server
│   ├── mcp_server.py          # MCP server
│   ├── history.py             # Protocol history
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ...
│   │   └── App.tsx            # Main app
│   └── package.json           # Node dependencies
├── docker-compose.yml         # Docker configuration
├── ARCHITECTURE.md            # Detailed architecture docs
└── README.md                  # This file
```

---

## 🏆 Evaluation Criteria Met

### 1. Architectural Ambition ✅
- **NOT a trivial chain**: Supervisor-Worker pattern with autonomous agents
- **Self-correcting**: Detects loops and halts appropriately
- **Complex reasoning**: Agents debate and refine internally
- **Autonomous**: Works without constant human intervention

### 2. State Hygiene ✅
- **Rich shared state**: Blackboard pattern with comprehensive state
- **Agent communication**: Notes and scratchpad for inter-agent communication
- **Version tracking**: Draft versions and edit history
- **Metadata**: Iteration counts, safety scores, empathy metrics

### 3. Persistence ✅
- **Full checkpointing**: Every node execution is checkpointed
- **Resume capability**: Can resume from any checkpoint
- **Human-in-the-loop**: Uses checkpoint state for seamless interruption/resumption
- **History logging**: All protocols stored in database

### 4. MCP Integration ✅
- **Complete implementation**: Full MCP server with tool exposure
- **Machine-to-machine**: Works with Claude Desktop and other MCP clients
- **Same backend logic**: MCP uses the same LangGraph workflow
- **Auto-approval**: MCP context bypasses human-in-the-loop (optional)

### 5. AI Leverage ✅
- **Comprehensive system**: Built with AI coding assistants (Cursor, Claude)
- **Rapid development**: Delivered "weeks worth of work" in 5 days
- **Complex architecture**: Multi-agent system with persistence and streaming

---

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Detailed system architecture and agent design
- **[DOCKER.md](./DOCKER.md)**: Docker setup and deployment
- **[LOCAL_MCP_SETUP.md](./LOCAL_MCP_SETUP.md)**: MCP server setup guide

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
