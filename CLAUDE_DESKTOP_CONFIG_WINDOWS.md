# Claude Desktop MCP Configuration for Windows

## Your Configuration

Based on your SSH config:
- **Host**: Sachit
- **HostName**: 47.236.14.170
- **User**: root
- **IdentityFile**: C:\Users\Turium AI\Downloads\turium_new_ali 2.pem

## Step 1: Locate Claude Desktop Config File

On Windows, the config file is located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Full path (usually):
```
C:\Users\Turium AI\AppData\Roaming\Claude\claude_desktop_config.json
```

## Step 2: Create/Edit the Config File

Open the file in a text editor (create it if it doesn't exist) and add:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "ssh",
      "args": [
        "Sachit",
        "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

## Step 3: Replace Placeholder

**IMPORTANT**: Replace `"your_openai_api_key_here"` with your actual OpenAI API key.

## Step 4: Alternative - Using Wrapper Script (More Reliable)

If the direct SSH command doesn't work, create a wrapper script:

### Create: `C:\Users\Turium AI\cerina-mcp.bat`

```batch
@echo off
setlocal
set OPENAI_API_KEY=%1
ssh Sachit "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='%OPENAI_API_KEY%' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
```

Then use this in Claude Desktop config:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "C:\\Users\\Turium AI\\cerina-mcp.bat",
      "args": [
        "your_openai_api_key_here"
      ]
    }
  }
}
```

## Step 5: Restart Claude Desktop

1. **Quit Claude Desktop completely** (not just close the window)
2. **Restart Claude Desktop**
3. The MCP server should connect automatically

## Step 6: Test Connection

In Claude Desktop, try:
```
Ask Cerina Foundry to create an exposure hierarchy for agoraphobia.
```

## Troubleshooting

### Issue: SSH not found
- Make sure Git Bash or OpenSSH is installed
- Or use full path: `"C:\\Program Files\\Git\\usr\\bin\\ssh.exe"`

### Issue: Python not found on remote
- Use full Python path: `/usr/bin/python3` instead of `python`

### Issue: Permission denied
- Check SSH key permissions
- Verify the PEM file path is correct

### Issue: Connection timeout
- Verify the instance is accessible: `ssh Sachit`
- Check firewall settings

## Quick Copy-Paste Config

Here's the ready-to-use config (just replace the API key):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "ssh",
      "args": [
        "Sachit",
        "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "REPLACE_WITH_YOUR_ACTUAL_KEY"
      }
    }
  }
}
```


