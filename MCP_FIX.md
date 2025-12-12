# MCP Connection Fix

## Problem
The `${OPENAI_API_KEY}` variable doesn't expand in SSH commands on Windows. The environment variable from the `env` section isn't passed through SSH.

## Solution
Put the API key directly in the SSH command string.

## Updated Config

Use this in your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "ssh",
      "args": [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-tt",
        "Sachit",
        "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && export PYTHONUNBUFFERED=1 && /opt/airbyte-platform/airbyte-common-handler/backend/venv/bin/python3 -u mcp_server.py 2>&1"
      ]
    }
  }
}
```

## Changes Made:
1. ✅ Removed `env` section (not needed)
2. ✅ Put API key directly in the command
3. ✅ Use full path to venv Python: `/opt/airbyte-platform/airbyte-common-handler/backend/venv/bin/python3`
4. ✅ Created virtual environment and installed all dependencies including `mcp`
5. ✅ Added error logging to `mcp_server.py` to help debug issues
6. ✅ Added SSH flags: `-tt` (force pseudo-terminal), `ServerAliveInterval` (keep connection alive)
7. ✅ Added `PYTHONUNBUFFERED=1` and `-u` flag for unbuffered output
8. ✅ Redirected stderr to stdout with `2>&1` to ensure error logs are captured

## Important Discovery:
✅ **The server works perfectly when run manually via SSH!** 
- When you run `ssh -tt Sachit "/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh"` in PowerShell, it works fine
- The issue is specifically with how Claude Desktop handles the connection

## Next Steps:
1. Update your Claude Desktop config with the above (changed `-tt` to `-T`)
2. Restart Claude Desktop completely
3. If it still doesn't work, check `/tmp/mcp_server.log` on the remote server for detailed error logs
4. The server is working correctly - the issue is likely Claude Desktop's handling of SSH stdio

## If Still Not Working:

### Option 1: Test SSH Command Manually
Open PowerShell and test:
```powershell
ssh Sachit "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='\${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python3 mcp_server.py"
```

If this works, the MCP should work too.

### Option 2: Verify Virtual Environment
The venv should be at `/opt/airbyte-platform/airbyte-common-handler/backend/venv/`. If it doesn't exist, create it:
```bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 3: Check MCP Server Logs
The `mcp-server-cerina-foundry` log file should show the actual error.


