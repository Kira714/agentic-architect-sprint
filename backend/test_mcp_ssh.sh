#!/bin/bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
export OPENAI_API_KEY='${OPENAI_API_KEY}'
export DATABASE_URL='postgresql+asyncpg://mcp_user:mcp_password@localhost:8008/mcp_chatbot_db'
export PYTHONUNBUFFERED=1
exec venv/bin/python3 -u mcp_server.py
