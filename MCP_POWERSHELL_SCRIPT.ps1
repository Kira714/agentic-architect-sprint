ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o LogLevel=ERROR -o ServerAliveInterval=60 -o ServerAliveCountMax=3 Sachit "/opt/airbyte-platform/airbyte-common-handler/backend/run_mcp_server.sh"

