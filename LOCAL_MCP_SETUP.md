# Local MCP Server Setup (No SSH Required)

This guide shows how to set up and test the MCP server locally on your Windows machine, avoiding SSH stdio issues.

## Prerequisites

1. **Python 3.10+** installed on Windows
2. **Git** installed
3. **OpenAI API Key**

## Step 1: Clone the Repository

```powershell
git clone https://github.com/Kira714/agentic-architect-sprint.git
cd agentic-architect-sprint
```

## Step 2: Set Up Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Configure Environment

Create `backend/.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./cerina_foundry.db
```

## Step 4: Test MCP Server Locally

Test the server directly:

```powershell
cd backend
.\venv\Scripts\activate
python mcp_server.py
```

You should see `[MCP INFO]` messages. Press Ctrl+C to stop.

## Step 5: Configure Claude Desktop (Local)

Update your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": ["C:\\path\\to\\agentic-architect-sprint\\backend\\mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "DATABASE_URL": "sqlite+aiosqlite:///./cerina_foundry.db"
      }
    }
  }
}
```

**Important:** Use the full absolute path to `mcp_server.py`.

## Step 6: Alternative - Use Virtual Environment Python

If the above doesn't work, use the venv Python directly:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "C:\\path\\to\\agentic-architect-sprint\\backend\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\agentic-architect-sprint\\backend\\mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "DATABASE_URL": "sqlite+aiosqlite:///./cerina_foundry.db"
      }
    }
  }
}
```

## Step 7: Restart Claude Desktop

1. Close all Claude Desktop windows
2. Reopen Claude Desktop
3. Check the MCP server connection in logs

## Troubleshooting

### Import Errors
- Make sure virtual environment is activated
- Verify all dependencies are installed: `pip list | grep mcp`

### Path Issues
- Use forward slashes or double backslashes in paths: `C:\\path\\to\\file.py`
- Use absolute paths, not relative paths

### Database Issues
- The SQLite database will be created automatically in the backend directory
- If you get database errors, delete `cerina_foundry.db` and restart

## Testing the MCP Tool

Once connected, try asking Claude:
```
Use the cerina-foundry tool to create a sleep hygiene protocol for insomnia.
```

Or:
```
Create a CBT exercise for managing anxiety using the cerina-foundry MCP server.
```

## Benefits of Local Setup

✅ No SSH stdio forwarding issues
✅ Faster development and testing
✅ Easier debugging (can see all logs)
✅ No network dependency
✅ Works reliably on Windows

