# Routing Explanation - Where Routing Happens

## 🔄 Routing Flow Overview

Routing in the Personal MCP Chatbot happens in **3 key locations**:

```
1. Supervisor Agent (backend/agents/supervisor.py)
   ↓ Sets next_action in state
   
2. route_decision() function (backend/graph.py)
   ↓ Reads next_action from state
   
3. LangGraph conditional_edges (backend/graph.py)
   ↓ Routes to appropriate node based on decision
```

---

## 📍 Location 1: Supervisor Agent - Decision Making

**File**: `backend/agents/supervisor.py`  
**Function**: `supervisor_node()`  
**Lines**: 193-241

### What Happens Here:

1. **Supervisor analyzes state** (lines 48-100)
   - Checks if draft exists
   - Checks safety review status
   - Checks clinical review status
   - Checks debate completion
   - Checks iteration count

2. **Supervisor makes routing decision** (lines 103-183)
   - Uses LLM to decide next step
   - Extracts decision from LLM response
   - Validates decision against valid options

3. **Fallback logic if invalid decision** (lines 193-210)
   - If LLM returns invalid decision, uses strict workflow sequence
   - Ensures routing always works

4. **Sets next_action in state** (line 241)
   ```python
   return {
       **state,
       "next_action": decision,  # ← ROUTING DECISION STORED HERE
       "agent_notes": state.get('agent_notes', []) + notes_to_add,
       "current_agent": AgentRole.SUPERVISOR,
       "last_updated": datetime.now().isoformat()
   }
   ```

**Key Code**:
```python
# Line 241 in supervisor.py
"next_action": decision,  # Store routing decision
```

---

## 📍 Location 2: route_decision() Function - Decision Extraction

**File**: `backend/graph.py`  
**Function**: `route_decision()`  
**Lines**: 142-170

### What Happens Here:

1. **Reads next_action from state** (line 166)
   ```python
   decision = state.get('next_action', 'draftsman')
   ```

2. **Clears next_action** (lines 168-169)
   ```python
   if 'next_action' in state:
       state['next_action'] = None
   ```

3. **Returns decision string** (line 170)
   - Returns: "draftsman", "safety_guardian", "clinical_critic", "debate_moderator", "halt", or "approve"

**Key Code**:
```python
# Lines 142-170 in graph.py
def route_decision(state: FoundryState) -> str:
    """Route based on supervisor's decision"""
    # Get the decision from the state (set by supervisor)
    decision = state.get('next_action', 'draftsman')
    # Clear it for next iteration
    if 'next_action' in state:
        state['next_action'] = None
    return decision
```

---

## 📍 Location 3: LangGraph Conditional Edges - Actual Routing

**File**: `backend/graph.py`  
**Function**: `create_foundry_graph()`  
**Lines**: 172-183

### What Happens Here:

1. **LangGraph uses conditional_edges** (lines 172-183)
   ```python
   workflow.add_conditional_edges(
       "supervisor",           # From node
       route_decision,         # Routing function
       {                       # Route mapping
           "draftsman": "draftsman",
           "safety_guardian": "safety_guardian",
           "clinical_critic": "clinical_critic",
           "debate_moderator": "debate_moderator",
           "halt": "halt",
           "approve": "approve"
       }
   )
   ```

2. **LangGraph executes routing**
   - After supervisor node completes
   - Calls `route_decision()` function
   - Gets decision string
   - Routes to corresponding node based on mapping

**Key Code**:
```python
# Lines 172-183 in graph.py
workflow.add_conditional_edges(
    "supervisor",
    route_decision,  # ← This function is called by LangGraph
    {
        "draftsman": "draftsman",           # If decision = "draftsman" → go to draftsman node
        "safety_guardian": "safety_guardian", # If decision = "safety_guardian" → go to safety_guardian node
        "clinical_critic": "clinical_critic", # etc...
        "debate_moderator": "debate_moderator",
        "halt": "halt",
        "approve": "approve"
    }
)
```

---

## 🔄 Complete Routing Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. SUPERVISOR NODE EXECUTES                             │
│    File: backend/agents/supervisor.py:15-241            │
│    • Analyzes state                                      │
│    • Makes routing decision (LLM or fallback)            │
│    • Sets next_action = "draftsman" (example)           │
│    • Returns updated state                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 2. LANGGRAPH CALLS route_decision()                     │
│    File: backend/graph.py:142-170                       │
│    • Reads state.get('next_action')                     │
│    • Gets decision = "draftsman"                        │
│    • Clears next_action                                 │
│    • Returns "draftsman"                                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 3. LANGGRAPH ROUTES TO NODE                             │
│    File: backend/graph.py:172-183                       │
│    • Looks up "draftsman" in route mapping              │
│    • Routes to "draftsman" node                         │
│    • Executes draftsman_node()                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Key Files and Line Numbers

### Supervisor Decision Making
- **File**: `backend/agents/supervisor.py`
- **Function**: `supervisor_node()` (line 15)
- **Decision Logic**: Lines 48-210
- **Sets next_action**: Line 241

### Routing Function
- **File**: `backend/graph.py`
- **Function**: `route_decision()` (line 142)
- **Reads next_action**: Line 166
- **Clears next_action**: Lines 168-169
- **Returns decision**: Line 170

### LangGraph Routing
- **File**: `backend/graph.py`
- **Function**: `create_foundry_graph()` (line 21)
- **Conditional edges setup**: Lines 172-183
- **Route mapping**: Lines 176-182

---

## 🎯 Summary

**Routing happens in 3 places**:

1. **Supervisor decides** (`supervisor.py:241`) → Sets `next_action` in state
2. **route_decision() extracts** (`graph.py:166`) → Reads `next_action` from state
3. **LangGraph routes** (`graph.py:172-183`) → Uses decision to route to node

**The routing decision flows**:
```
Supervisor → next_action in state → route_decision() → LangGraph → Target Node
```

---

## 💡 Important Notes

1. **Supervisor is the decision maker** - It analyzes state and decides where to route
2. **route_decision() is the bridge** - It extracts the decision from state for LangGraph
3. **LangGraph does the actual routing** - It uses conditional_edges to route to nodes
4. **All workers return to supervisor** - After completing, they go back to supervisor for next routing decision
5. **Fallback logic exists** - If LLM returns invalid decision, strict workflow sequence is used

---

**Quick Reference**:
- **Decision made**: `backend/agents/supervisor.py:241`
- **Decision read**: `backend/graph.py:166`
- **Routing executed**: `backend/graph.py:172-183`

