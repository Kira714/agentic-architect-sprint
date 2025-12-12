# Cerina Protocol Foundry - Architecture Documentation

## Overview

Cerina Protocol Foundry is a multi-agent system for creating evidence-based CBT (Cognitive Behavioral Therapy) exercises. It uses a **Supervisor-Worker pattern** with autonomous agents that debate, refine, and self-correct before presenting results to humans.

## Architecture Diagram

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
│    ┌────┴─────┬──────────┬──────────┬──────────┬──────────┐  │
│    │          │          │          │          │          │  │
│  ┌─▼──┐  ┌───▼──┐  ┌────▼───┐ ┌───▼────┐ ┌───▼─────┐    │  │
│  │Info│  │Draft │  │Safety  │ │Clinical│ │Debate   │    │  │
│  │Gath│  │sman  │  │Guardian│ │Critic  │ │Moderator│    │  │
│  └─┬──┘  └───┬──┘  └────┬───┘ └───┬────┘ └───┬─────┘    │  │
│    │         │          │         │          │          │  │
│    └─────────┴──────────┴─────────┴──────────┴──────────┘  │
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
│  - learned_patterns, adaptation_notes                         │
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

## Agent Architecture (Supervisor-Worker Pattern)

### 1. Supervisor Agent
- **Role**: Orchestrator and router
- **Responsibilities**:
  - Analyzes current state
  - Routes to appropriate agents
  - Detects loops and self-corrects
  - Decides when to halt for human review
- **Thinking Layer**: Makes routing decisions based on state analysis

### 2. Information Gatherer Agent
- **Role**: Context-aware information collection
- **Responsibilities**:
  - Analyzes if request is standard exercise vs personalized treatment
  - Asks questions ONLY when needed (emotional requests, vague requests)
  - Skips questions for standard CBT exercises
- **Thinking Layer 2**: Context-aware decision making

### 3. Draftsman Agent
- **Role**: Creates and edits CBT exercises
- **Responsibilities**:
  - Creates evidence-based, professional exercises
  - Edits shared document (blackboard pattern)
  - Incorporates feedback from reviews and debate
  - Ensures exercises surpass medical standards
- **Thinking Layer 3**: Evidence-based draft creation

### 4. Safety Guardian Agent
- **Role**: Safety reviewer
- **Responsibilities**:
  - Reviews for self-harm risks
  - Checks for medical advice
  - Identifies dangerous content
  - Ensures safety disclaimers
- **Thinking Layer 4**: Safety analysis

### 5. Clinical Critic Agent
- **Role**: Clinical quality evaluator
- **Responsibilities**:
  - Evaluates empathy, tone, structure
  - Assesses therapeutic effectiveness
  - Provides clinical feedback
  - Ensures medical standards compliance
- **Thinking Layer 5**: Clinical evaluation

### 6. Debate Moderator Agent
- **Role**: Facilitates internal debate
- **Responsibilities**:
  - Orchestrates debate between agents
  - Ensures evidence-based arguments
  - Reaches consensus on refinements
  - Final quality check before human review
- **Thinking Layer 6**: Internal debate and refinement

## State Management (Blackboard Pattern)

The `FoundryState` is a shared blackboard where all agents read and write:

- **Shared Document**: `current_draft` - all agents edit the same document
- **Communication**: `agent_notes` - agents leave notes for each other
- **Version Control**: `draft_versions`, `draft_edits` - tracks changes
- **Reviews**: `safety_review`, `clinical_review` - review results
- **Debate**: `agent_debate` - internal debate transcript
- **Learning**: `learned_patterns`, `adaptation_notes` - system learning

## Persistence & Checkpointing

### Checkpointing Strategy
1. **Every Node Execution**: State is checkpointed after each agent node
2. **Resume Capability**: Can resume from any checkpoint
3. **Human-in-the-Loop**: 
   - Workflow halts → state checkpointed
   - Human reviews → state fetched from checkpoint
   - Human approves → state updated in checkpoint
   - Workflow resumes from checkpoint

### Database Tables
- **LangGraph Checkpoints**: Managed by LangGraph checkpointer
- **Protocol History**: Stores all queries, protocols, and state snapshots

## Human-in-the-Loop Flow

1. **Workflow Execution**: Agents work, state checkpointed at each step
2. **Halt Trigger**: Supervisor decides to halt (max iterations, reviews complete, etc.)
3. **State Checkpointed**: Current state saved to database
4. **UI Fetches State**: `/api/protocols/{id}/state` gets state from checkpoint
5. **Human Reviews**: UI displays draft, human can edit
6. **Human Approves**: `/api/protocols/{id}/approve` updates checkpoint
7. **Workflow Resumes**: State updated, final protocol saved

## MCP Server Integration

The MCP server exposes the workflow as a tool:

- **Tool Name**: `create_cbt_protocol`
- **Input**: `user_query`, optional `user_specifics`, `max_iterations`
- **Output**: Final protocol JSON
- **Use Case**: Machine-to-machine communication (e.g., Claude Desktop)

## Key Features

1. **5-6 Thinking Layers**: Each agent has distinct thinking prompts
2. **Context Awareness**: Understands standard exercises vs personalized treatment
3. **Self-Correction**: Detects loops and halts appropriately
4. **Shared Document Editing**: Agents collaborate on same document
5. **Internal Debate**: Agents argue and refine before human review
6. **Checkpoint-Based Resume**: Human-in-the-loop uses database checkpoints
7. **History Logging**: All protocols stored in database

## Technology Stack

- **Backend**: Python, FastAPI, LangGraph
- **Database**: PostgreSQL (with SQLite fallback)
- **Checkpointing**: LangGraph Checkpointers (AsyncSqlAlchemySaver, AsyncPostgresSaver)
- **Frontend**: React, TypeScript, Vite
- **MCP**: mcp-python SDK
- **Streaming**: Server-Sent Events (SSE)


