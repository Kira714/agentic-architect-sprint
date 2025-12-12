# Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn
- OpenAI API key

## Quick Start

1. **Run setup script:**
```bash
./setup.sh
```

2. **Configure environment:**
```bash
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Start backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload
```

4. **Start frontend (in new terminal):**
```bash
cd frontend
npm run dev
```

5. **Access the dashboard:**
Open http://localhost:5173

## MCP Server Setup

1. **Install dependencies:**
```bash
cd mcp_server
source ../backend/venv/bin/activate
pip install -r requirements.txt
```

2. **Configure Claude Desktop:**
Add to your Claude Desktop MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_key_here",
        "DATABASE_URL": "sqlite+aiosqlite:///./cerina_foundry.db"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

## Testing

### Test Backend API:
```bash
curl -X POST http://localhost:8000/api/protocols/create \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Create an exposure hierarchy for agoraphobia"}'
```

### Test MCP Server:
In Claude Desktop, try:
```
Ask Cerina Foundry to create a sleep hygiene protocol for insomnia.
```

## Troubleshooting

### Database Issues
- Delete `cerina_foundry.db` to reset
- Check database permissions

### Import Errors
- Ensure virtual environment is activated
- Check Python path includes backend directory

### MCP Connection Issues
- Verify absolute path in Claude Desktop config
- Check environment variables are set
- Review MCP server logs





