#!/bin/bash
# Wrapper script for MCP server to ensure proper stdio handling via SSH

cd /opt/airbyte-platform/airbyte-common-handler/backend

# Export environment variables
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry}"

# Ensure unbuffered output
export PYTHONUNBUFFERED=1

# Use exec to replace shell process and ensure proper signal handling
# Don't redirect stderr - let it go to stderr so Claude Desktop can capture it
exec /opt/airbyte-platform/airbyte-common-handler/backend/venv/bin/python3 -u mcp_server.py

