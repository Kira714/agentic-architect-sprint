# MCP Connection Troubleshooting

## Quick Checks

### 1. Test SSH Connection Manually
Open PowerShell or Command Prompt and test:
```bash
ssh Sachit
```
If this works, SSH is configured correctly.

### 2. Test MCP Server on Remote
SSH into your instance and test the MCP server:
```bash
ssh Sachit
cd /opt/airbyte-platform/airbyte-common-handler/backend
export OPENAI_API_KEY='${OPENAI_API_KEY}'
export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry'
python mcp_server.py
```

If it starts without errors, the server is working.

### 3. Check Claude Desktop Logs
On Windows, check logs at:
```
%APPDATA%\Claude\logs\
```

Look for MCP-related errors.

## Common Issues

### Issue: "ssh: command not found"
**Solution**: Use full path to SSH:
```json
"command": "C:\\Windows\\System32\\OpenSSH\\ssh.exe",
```
Or if using Git Bash:
```json
"command": "C:\\Program Files\\Git\\usr\\bin\\ssh.exe",
```

### Issue: "Python not found"
**Solution**: Use full Python path in the SSH command:
```json
"args": [
  "Sachit",
  "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && /usr/bin/python3 mcp_server.py"
]
```

### Issue: Environment variable not passed
**Solution**: The `${OPENAI_API_KEY}` might not expand. Try this alternative:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "ssh",
      "args": [
        "Sachit",
        "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
      ]
    }
  }
}
```

### Issue: Connection timeout
**Solution**: 
- Verify instance is accessible: `ping 47.236.14.170`
- Check firewall settings
- Ensure SSH port (22) is open

### Issue: Tool not appearing
**Solution**:
1. Verify JSON is valid (use a JSON validator)
2. Ensure Claude Desktop is fully restarted
3. Check Claude Desktop logs for errors
4. Try removing and re-adding the MCP server config

## Alternative: Wrapper Script Method

If direct SSH doesn't work, create a wrapper:

**Create**: `C:\Users\Turium AI\cerina-mcp.bat`
```batch
@echo off
ssh Sachit "cd /opt/airbyte-platform/airbyte-common-handler/backend && export OPENAI_API_KEY='\${OPENAI_API_KEY}' && export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry' && python mcp_server.py"
```

Then update Claude Desktop config:
```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "C:\\Users\\Turium AI\\cerina-mcp.bat"
    }
  }
}
```

## Success Indicators

When it's working, you should:
1. See no errors in Claude Desktop
2. Be able to use: "Ask Cerina Foundry to create..."
3. Get a response with a CBT protocol


