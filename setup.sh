#!/bin/bash

echo "🧠 Setting up Cerina Protocol Foundry..."

# Backend setup
echo "📦 Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Frontend setup
echo "📦 Setting up React frontend..."
cd frontend
npm install
cd ..

# MCP Server setup
echo "📦 Setting up MCP server..."
cd mcp_server
if [ -d "../backend/venv" ]; then
    source ../backend/venv/bin/activate
fi
pip install -r requirements.txt
cd ..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create backend/.env with OPENAI_API_KEY"
echo "2. Run backend: cd backend && source venv/bin/activate && python -m uvicorn main:app --reload"
echo "3. Run frontend: cd frontend && npm run dev"
echo "4. Access at http://localhost:5173"





