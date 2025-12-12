# Chatbox MCP Server Setup

## Option 1: Local (stdio) - Recommended

### Setup Steps:

1. **Create a local Python wrapper script on Windows:**

   Create `C:\mcp_chatbox_wrapper.py`:
   ```python
   import subprocess
   import sys
   
   # Run SSH command and forward stdio
   cmd = [
       "C:\\Windows\\System32\\OpenSSH\\ssh.exe",
       "-T",
       "-o", "StrictHostKeyChecking=no",
       "-o", "UserKnownHostsFile=NUL",
       "-o", "LogLevel=ERROR",
       "Sachit",
       "/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh"
   ]
   
   process = subprocess.Popen(
       cmd,
       stdin=sys.stdin,
       stdout=sys.stdout,
       stderr=sys.stderr,
       bufsize=0
   )
   process.wait()
   ```

2. **In Chatbox, configure:**
   - **Name:** `cerina-foundry`
   - **Type:** `Local (stdio)`
   - **Command:** `python`
   - **Args:** `C:\mcp_chatbox_wrapper.py`

### Alternative: Direct SSH (if Chatbox supports it)

If Chatbox allows direct command execution:
- **Command:** `ssh`
- **Args:** `-T`, `-o`, `StrictHostKeyChecking=no`, `-o`, `UserKnownHostsFile=NUL`, `Sachit`, `/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh`

---

## Option 2: Remote (HTTP/SSE) - More Complex

This requires setting up an HTTP/SSE MCP server. The current server is stdio-based, so we'd need to add HTTP endpoints.

### If you want to try Remote:

You would need to:
1. Add HTTP/SSE transport to the MCP server
2. Expose it on a port (e.g., `http://your-server:8001/mcp`)
3. Configure Chatbox with:
   - **Type:** `Remote (http/sse)`
   - **URL:** `http://your-server-ip:8001/mcp`

**Note:** This requires additional development to add HTTP/SSE support to the MCP server.

---

## Recommended: Try Option 1 First

The Python wrapper script should handle stdio forwarding better than batch files. Make sure you have Python installed on Windows and can run `python` from command line.

