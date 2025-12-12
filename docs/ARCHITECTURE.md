# Cerina Protocol Foundry - Architecture

## System Overview

The Cerina Protocol Foundry is an autonomous multi-agent system that designs, critiques, and refines CBT (Cognitive Behavioral Therapy) exercises. It uses a **Supervisor-Worker** pattern with specialized agents that collaborate through a shared state (Blackboard pattern).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
├─────────────────────┬───────────────────────────────────────┤
│   React Dashboard   │         MCP Server                     │
│  (Human-in-Loop)    │      (Machine-to-Machine)              │
└──────────┬──────────┴──────────────┬─────────────────────────┘
           │                         │
           │ HTTP/SSE                │ MCP Protocol
           │                         │
┌──────────▼─────────────────────────▼─────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LangGraph Workflow                      │   │
│  │                                                       │   │
│  │  ┌──────────────┐                                    │   │
│  │  │  Supervisor  │◄──────────────────────┐           │   │
│  │  │   (Router)   │                        │           │   │
│  │  └──────┬───────┘                        │           │   │
│  │         │                                 │           │   │
│  │    ┌────▼─────┐  ┌──────────┐  ┌────────▼──┐        │   │
│  │    │Draftsman │  │  Safety  │  │ Clinical  │        │   │
│  │    │          │  │ Guardian │  │  Critic   │        │   │
│  │    └────┬─────┘  └────┬─────┘  └─────┬────┘        │   │
│  │         │             │              │              │   │
│  │         └────────────┴──────────────┘              │   │
│  │                      │                              │   │
│  │                      ▼                              │   │
│  │            ┌─────────────────┐                     │   │
│  │            │  Shared State   │                     │   │
│  │            │  (Blackboard)    │                     │   │
│  │            └─────────────────┘                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         LangGraph Checkpointer                       │   │
│  │         (SQLite/Postgres)                            │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## Agent Architecture

### Supervisor Agent
- **Role**: Orchestrates the workflow and makes routing decisions
- **Responsibilities**:
  - Decides which agent should act next
  - Monitors iteration count and halts when needed
  - Routes to appropriate workers based on current state

### Draftsman Agent
- **Role**: Creates and revises CBT exercise drafts
- **Responsibilities**:
  - Generates initial drafts based on user intent
  - Incorporates feedback from Safety Guardian and Clinical Critic
  - Maintains version history

### Safety Guardian Agent
- **Role**: Reviews drafts for safety concerns
- **Responsibilities**:
  - Flags self-harm risks
  - Identifies medical advice that should be left to professionals
  - Ensures safety disclaimers are present
  - Provides recommendations for revision

### Clinical Critic Agent
- **Role**: Evaluates clinical quality
- **Responsibilities**:
  - Assesses empathy and warmth (0-10 scale)
  - Evaluates tone appropriateness (0-10 scale)
  - Reviews structure and clarity (0-10 scale)
  - Provides constructive feedback

## State Management (Blackboard Pattern)

The `FoundryState` TypedDict serves as the shared blackboard where all agents read from and write to:

- **User Input**: Original query and intent
- **Draft Management**: Current draft, version history
- **Agent Communications**: Notes left by agents for each other
- **Reviews**: Safety and clinical review results
- **Workflow Control**: Iteration count, halt status, approval status
- **Human-in-the-Loop**: Feedback and edited drafts

## Workflow Flow

1. **User submits query** → Initial state created
2. **Supervisor routes** → Decides first action (usually Draftsman)
3. **Draftsman creates draft** → Writes to shared state
4. **Safety Guardian reviews** → Flags concerns if any
5. **Clinical Critic evaluates** → Provides quality scores
6. **Supervisor decides**:
   - If concerns → Route back to Draftsman for revision
   - If passed → Halt for human approval
   - If max iterations → Halt for human review
7. **Human reviews** → Edits and approves
8. **Workflow resumes** → Finalizes protocol

## Persistence & Checkpointing

- **LangGraph Checkpointers**: Every graph step is checkpointed to SQLite
- **Resume Capability**: Server crashes don't lose progress
- **State Retrieval**: Human-in-the-loop can fetch current state from checkpoint
- **History**: All past protocols stored in database

## Human-in-the-Loop Mechanism

1. Workflow halts when:
   - Safety/Clinical reviews pass
   - Max iterations reached
   - Supervisor decides human review needed

2. React UI:
   - Fetches current state from checkpoint
   - Displays draft for review
   - Allows editing
   - Collects feedback

3. Upon approval:
   - State updated with human input
   - Workflow resumes
   - Final protocol saved

## MCP Integration

The MCP server exposes the workflow as a single tool:
- **Tool Name**: `create_cbt_protocol`
- **Input**: User query, optional intent and max iterations
- **Output**: Generated protocol with metadata
- **Use Case**: Machine-to-machine integration (e.g., Claude Desktop)

## Technology Stack

- **Backend**: Python 3.10+, LangGraph, LangChain, FastAPI
- **Frontend**: React 18, TypeScript, Vite
- **Database**: SQLite (with Postgres support)
- **MCP**: Model Context Protocol SDK
- **LLM**: OpenAI GPT-4 (configurable)

## Key Design Decisions

1. **Supervisor-Worker Pattern**: Provides clear orchestration and autonomy
2. **Blackboard State**: Enables rich agent-to-agent communication
3. **Checkpointing**: Ensures reliability and resumability
4. **SSE Streaming**: Real-time updates to React frontend
5. **MCP Integration**: Enables interoperability with MCP ecosystem





