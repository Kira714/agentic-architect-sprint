# Cerina Protocol Foundry

An intelligent multi-agent system that autonomously designs, critiques, and refines CBT (Cognitive Behavioral Therapy) exercises.

## 🎯 Overview

The Cerina Protocol Foundry uses a **Supervisor-Worker** pattern with specialized AI agents that collaborate through a shared state (Blackboard pattern) to create safe, empathetic, and clinically sound CBT exercises.

## 🏗️ Architecture

### Agent System
- **Supervisor**: Orchestrates workflow and makes routing decisions
- **Draftsman**: Creates and revises CBT exercise drafts
- **Safety Guardian**: Reviews for safety concerns (self-harm, medical advice)
- **Clinical Critic**: Evaluates tone, empathy, and clinical quality

### Key Features
- ✅ **Autonomous Multi-Agent System**: Agents debate and refine internally
- ✅ **Deep State Management**: Rich shared state with agent notes and version history
- ✅ **Persistence & Checkpointing**: Resume from any point using SQLite
- ✅ **Human-in-the-Loop**: Interrupt workflow for human review and approval
- ✅ **Real-Time Visualization**: React dashboard with live agent activity
- ✅ **MCP Integration**: Expose workflow as MCP tool for machine-to-machine use

## 📁 Project Structure

```
.
├── backend/              # Python LangGraph backend
│   ├── agents/          # Agent implementations
│   ├── state.py         # State schema (Blackboard)
│   ├── graph.py         # LangGraph workflow
│   ├── database.py      # Checkpointing setup
│   └── main.py          # FastAPI server
├── frontend/            # React TypeScript frontend
│   └── src/
│       ├── components/  # UI components
│       └── App.tsx      # Main app
├── mcp_server/          # MCP server
│   └── mcp_server.py    # MCP tool implementation
└── docs/                # Documentation
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Access Dashboard:**
- Frontend: http://localhost:8006
- Backend API: http://localhost:8005
- API Docs: http://localhost:8005/docs
- PostgreSQL: localhost:8007

See [DOCKER.md](./DOCKER.md) for detailed Docker instructions.

### Option 2: Local Development

1. **Setup:**
```bash
./setup.sh
```

2. **Configure:**
Create `backend/.env`:
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite+aiosqlite:///./cerina_foundry.db
```

3. **Run Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload
```

4. **Run Frontend:**
```bash
cd frontend
npm run dev
```

5. **Access Dashboard:**
Open http://localhost:5173

## 📖 Usage

### React Dashboard

1. Enter a query (e.g., "Create an exposure hierarchy for agoraphobia")
2. Watch agents work in real-time
3. Review the draft when workflow halts
4. Edit if needed and approve to finalize

### MCP Server

Configure Claude Desktop to use the MCP server (see `docs/SETUP.md`), then:

```
Ask Cerina Foundry to create a sleep hygiene protocol for insomnia.
```

## 🔧 Technology Stack

- **Backend**: Python 3.10+, LangGraph, LangChain, FastAPI
- **Frontend**: React 18, TypeScript, Vite
- **Database**: SQLite (with Postgres support)
- **MCP**: Model Context Protocol SDK
- **LLM**: OpenAI GPT-4 (configurable)

## 📚 Documentation

- [Architecture](./docs/ARCHITECTURE.md) - System design and agent architecture
- [Setup Guide](./docs/SETUP.md) - Detailed setup instructions

## 🎬 Demo Scenarios

### Scenario 1: Basic Protocol Creation
1. Query: "Create a cognitive restructuring exercise for anxiety"
2. Agents collaborate: Draftsman → Safety Guardian → Clinical Critic
3. Human reviews and approves
4. Final protocol saved

### Scenario 2: Iterative Refinement
1. Safety Guardian flags a concern
2. Supervisor routes back to Draftsman
3. Draftsman revises based on feedback
4. Process repeats until all reviews pass

### Scenario 3: MCP Integration
1. User prompts Claude Desktop
2. MCP server triggers workflow
3. Protocol generated autonomously
4. Result returned to Claude

## 🏆 Evaluation Criteria Met

✅ **Architectural Ambition**: Supervisor-Worker with autonomous agents  
✅ **State Hygiene**: Rich Blackboard pattern with agent notes  
✅ **Persistence**: Full checkpointing with resume capability  
✅ **MCP Integration**: Complete MCP server implementation  
✅ **AI Leverage**: Comprehensive system built with AI assistance  

## 📝 License

This project is built for the Cerina Protocol Foundry challenge.
