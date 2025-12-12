#!/bin/bash
cd /opt/airbyte-platform/airbyte-common-handler/backend
export OPENAI_API_KEY='${OPENAI_API_KEY}'
export DATABASE_URL='postgresql+asyncpg://cerina:cerina_password@localhost:8008/cerina_foundry'
export PYTHONUNBUFFERED=1
exec venv/bin/python3 -u mcp_server.py
