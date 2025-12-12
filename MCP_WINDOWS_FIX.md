# MCP Server Windows SSH Fix

## The Problem
Claude Desktop on Windows connects via SSH but immediately closes the connection after initialization. The server works perfectly when run manually via SSH.

## Root Cause
Claude Desktop on Windows has issues with SSH stdio forwarding. The stderr output isn't being captured, and the connection closes prematurely.

## Solution: Use a Local Wrapper Script

Since SSH stdio forwarding is problematic on Windows, we need to create a local wrapper script that Claude Desktop can run directly.

### Step 1: Create a Local Wrapper Script (Windows)

Create a file at `C:\mcp_server_wrapper.bat` (or `C:\Users\Turium AI\mcp_server_wrapper.bat`):

```batch
@echo off
setlocal
set PYTHONUNBUFFERED=1
ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR -o ServerAliveInterval=60 -o ServerAliveCountMax=3 Sachit "/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh"
```

**IMPORTANT:** Make sure the batch file doesn't have any extra output. The `@echo off` prevents echo, but we need to ensure nothing else interferes with stdio.

### Step 2: Update Claude Desktop Config

Update your `claude_desktop_config.json` (note the quotes around the path due to space in "Turium AI"):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "\"C:\\Users\\Turium AI\\mcp_server_wrapper.bat\""
    }
  }
}
```

**OR** use the `args` approach which handles spaces better:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "cmd",
      "args": ["/c", "C:\\Users\\Turium AI\\mcp_server_wrapper.bat"]
    }
  }
}
```

### Alternative: Use PowerShell Script

If the batch file doesn't work, try a PowerShell script at `C:\Users\Turium AI\mcp_server_wrapper.ps1`:

```powershell
ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR Sachit "/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh"
```

And update the config:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "powershell",
      "args": ["-File", "C:\\Users\\Turium AI\\mcp_server_wrapper.ps1"]
    }
  }
}
```

### Step 3: Test the Wrapper

Test the wrapper script manually first:

```powershell
C:\Users\Turium AI\mcp_server_wrapper.bat
```

You should see the `[MCP INFO]` messages. If you do, the wrapper works and Claude Desktop should be able to use it.

## Why This Might Work

By using a local wrapper script instead of having Claude Desktop construct the SSH command directly, we:
1. Avoid potential quoting/escaping issues
2. Give Claude Desktop a simpler command to execute
3. Let the wrapper handle all SSH complexity

## If Still Not Working

If this still doesn't work, the issue is likely a fundamental limitation of Claude Desktop's SSH stdio handling on Windows. In that case, consider:

1. **Run MCP server locally** (if possible)
2. **Use a different transport** (TCP socket instead of stdio)
3. **File a bug report** with Anthropic about Windows SSH stdio issues

