# MCP Server Setup Guide

This guide explains how to connect the Cerina Protocol Foundry MCP server to Claude Desktop or other MCP clients.

## Prerequisites

1. **Python 3.10+** installed
2. **MCP Python SDK** installed (`pip install mcp`)
3. **OpenAI API Key** configured
4. **Claude Desktop** installed (for Claude Desktop connection)

## Step 1: Verify MCP Server File

The MCP server is located at:
```
/opt/airbyte-platform/airbyte-common-handler/backend/mcp_server.py
```

## Step 2: Install Dependencies

Make sure all dependencies are installed in your Python environment:

```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
pip install mcp langgraph langchain langchain-openai sqlalchemy asyncpg psycopg2-binary python-dotenv
```

## Step 3: Set Environment Variables

Create or update `.env` file in the backend directory:

```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry
# Or for SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./cerina_foundry.db
EOF
```

## Step 4: Test MCP Server Standalone

Test that the MCP server runs correctly:

```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
python mcp_server.py
```

The server should start and wait for stdio input. Press Ctrl+C to exit.

## Step 5: Configure Claude Desktop

### For macOS:

1. Open Claude Desktop configuration file:
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or create it if it doesn't exist:
```bash
mkdir -p ~/Library/Application\ Support/Claude
touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": [
        "/opt/airbyte-platform/airbyte-common-handler/backend/mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "DATABASE_URL": "postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry"
      }
    }
  }
}
```

**Important**: Replace:
- `your_openai_api_key_here` with your actual OpenAI API key
- The `DATABASE_URL` if using a different database setup
- The path to `mcp_server.py` if your installation is in a different location

### For Windows:

1. Open Claude Desktop configuration file:
```
%APPDATA%\Claude\claude_desktop_config.json
```

2. Add the same configuration as above, but use Windows-style paths:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": [
        "C:\\path\\to\\airbyte-common-handler\\backend\\mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "DATABASE_URL": "postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry"
      }
    }
  }
}
```

### For Linux:

1. Open Claude Desktop configuration file:
```bash
~/.config/Claude/claude_desktop_config.json
```

2. Add the same configuration as macOS.

## Step 6: Restart Claude Desktop

After updating the configuration:
1. **Quit Claude Desktop completely** (not just close the window)
2. **Restart Claude Desktop**
3. The MCP server should connect automatically

## Step 7: Verify Connection

In Claude Desktop, you should see the `create_cbt_protocol` tool available. Test it with:

```
Ask Cerina Foundry to create an exposure hierarchy for agoraphobia.
```

Or:

```
Use the create_cbt_protocol tool to create a cognitive restructuring exercise for anxiety.
```

## Step 8: Using the Tool

The MCP tool accepts the following parameters:

- **user_query** (required): The CBT exercise request
  - Example: "Create an exposure hierarchy for agoraphobia"
  - Example: "Create a thought record exercise for depression"

- **user_specifics** (optional): User-specific information for personalization
  - Example: `{"severity": "moderate", "triggers": ["crowds", "public transport"]}`

- **max_iterations** (optional): Maximum workflow iterations (default: 10)

## Troubleshooting

### Issue: MCP server not connecting

**Solution 1**: Check Python path
```bash
which python
# Make sure the path in claude_desktop_config.json matches this
```

**Solution 2**: Test MCP server manually
```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
python mcp_server.py
# Should start without errors
```

**Solution 3**: Check environment variables
```bash
# Verify .env file exists and has correct values
cat backend/.env
```

**Solution 4**: Check Claude Desktop logs
- macOS: `~/Library/Logs/Claude/`
- Windows: `%APPDATA%\Claude\logs\`
- Linux: `~/.local/share/Claude/logs/`

### Issue: Import errors

**Solution**: Install missing dependencies
```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
pip install -r requirements.txt
pip install mcp
```

### Issue: Database connection errors

**Solution**: 
1. Ensure PostgreSQL is running (if using PostgreSQL)
2. Check DATABASE_URL in .env matches your database setup
3. For SQLite, ensure the directory is writable

### Issue: Tool not appearing in Claude Desktop

**Solution**:
1. Verify the configuration JSON is valid (use a JSON validator)
2. Ensure Claude Desktop is fully restarted
3. Check Claude Desktop logs for MCP connection errors

## Alternative: Using with Other MCP Clients

If you're using a different MCP client (not Claude Desktop), the setup is similar:

1. Configure the client to use stdio transport
2. Point to the MCP server script: `/opt/airbyte-platform/airbyte-common-handler/backend/mcp_server.py`
3. Set environment variables (OPENAI_API_KEY, DATABASE_URL)
4. The server communicates via stdio (standard input/output)

## Example Usage in Claude Desktop

Once connected, you can use natural language:

```
Create a CBT exercise for managing panic attacks using exposure therapy.
```

Or be more specific:

```
Ask Cerina Foundry to create a behavioral activation plan for someone with depression who has trouble getting out of bed.
```

The MCP server will:
1. Run the multi-agent workflow
2. Generate an evidence-based CBT exercise
3. Return the complete protocol as JSON

## Notes

- The MCP server runs the **same workflow** as the web interface
- It uses **checkpointing** for state persistence
- It **auto-approves** drafts (no human-in-the-loop for MCP)
- All protocols are **saved to the database** for history


