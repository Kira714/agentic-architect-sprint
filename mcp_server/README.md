# Cerina Foundry MCP Server

MCP (Model Context Protocol) server that exposes the Cerina Protocol Foundry as a tool.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (create `.env` file):
```
OPENAI_API_KEY=your_key_here
DATABASE_URL=sqlite+aiosqlite:///./cerina_foundry.db
```

## Usage

### With Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": ["/path/to/mcp_server/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Tool: create_cbt_protocol

Creates a CBT exercise protocol using the autonomous multi-agent system.

**Parameters:**
- `user_query` (required): The user's request
- `user_intent` (optional): Extracted intent
- `max_iterations` (optional): Max iterations (default: 10)

**Example:**
```
Ask Cerina Foundry to create a sleep hygiene protocol for insomnia.
```





