# MCP Remote Connection Setup (Instance to Local Desktop)

## YES - It's Possible!

You can connect Claude Desktop (local) to the MCP server running on your remote instance using **SSH**.

## Solution: SSH-Based MCP Connection

### Step 1: Set Up SSH Access

Ensure you can SSH into your instance from your local machine:

```bash
# Test SSH connection
ssh user@your-instance-ip
```

If you use SSH keys, make sure they're set up:
```bash
# Generate key if needed
ssh-keygen -t rsa

# Copy to instance
ssh-copy-id user@your-instance-ip
```

### Step 2: Configure Claude Desktop for Remote MCP

**macOS**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`

**Linux**: Edit `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "ssh",
      "args": [
        "user@your-instance-ip",
        "-o", "StrictHostKeyChecking=no",
        "cd /opt/airbyte-platform/airbyte-common-handler/backend && python mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_key_here"
      }
    }
  }
}
```

**OR** use a wrapper script approach (more reliable):

### Step 3: Create Local Wrapper Script (Better Approach)

Create a local script that handles the SSH connection:

**macOS/Linux**: `~/cerina-mcp-wrapper.sh`
```bash
#!/bin/bash
ssh user@your-instance-ip \
  -o StrictHostKeyChecking=no \
  "cd /opt/airbyte-platform/airbyte-common-handler/backend && \
   export OPENAI_API_KEY='$OPENAI_API_KEY' && \
   export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && \
   python mcp_server.py"
```

Make it executable:
```bash
chmod +x ~/cerina-mcp-wrapper.sh
```

**Windows**: `%USERPROFILE%\cerina-mcp-wrapper.bat`
```batch
@echo off
ssh user@your-instance-ip -o StrictHostKeyChecking=no "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='%OPENAI_API_KEY%' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
```

### Step 4: Update Claude Desktop Config

Use the wrapper script in Claude Desktop config:

**macOS/Linux**:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "/Users/yourusername/cerina-mcp-wrapper.sh",
      "env": {
        "OPENAI_API_KEY": "your_openai_key_here"
      }
    }
  }
}
```

**Windows**:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "C:\\Users\\YourUsername\\cerina-mcp-wrapper.bat",
      "env": {
        "OPENAI_API_KEY": "your_openai_key_here"
      }
    }
  }
}
```

### Step 5: Restart Claude Desktop

Quit and restart Claude Desktop completely.

## Alternative: Network-Based MCP Server (Advanced)

If SSH doesn't work well, we can modify the MCP server to use HTTP/SSE transport instead of stdio. This would require:

1. Creating an HTTP endpoint for MCP
2. Running the server on the instance
3. Connecting from local via HTTP

Would you like me to implement this alternative?

## Troubleshooting Remote Connection

### Issue: SSH connection fails

**Solution**: 
- Test SSH manually: `ssh user@instance-ip`
- Check SSH keys are set up
- Verify user has access to the instance

### Issue: Python not found on remote

**Solution**: Use full path to Python:
```bash
/usr/bin/python3 /opt/airbyte-platform/airbyte-common-handler/backend/mcp_server.py
```

### Issue: Environment variables not passed

**Solution**: Use the wrapper script approach and export variables explicitly in the SSH command.

### Issue: Database connection fails

**Solution**: Ensure the database is accessible from the instance (not just localhost). Update DATABASE_URL if needed.

## Quick Test

After setup, test in Claude Desktop:
```
Ask Cerina Foundry to create an exposure hierarchy for agoraphobia.
```

If it works, you'll see the protocol generated from your remote instance!


