# Development Setup Guide

## Port Configuration

The system uses the following ports (8005-8010 range):

- **8005**: Backend API (FastAPI)
- **8006**: Frontend (React/Vite)
- **8007**: PostgreSQL Database

## Quick Start - Development Mode

### 1. Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Required in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start Development Services

```bash
# Start in development mode with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use the Makefile
make dev
```

This will:
- Start PostgreSQL on port 8007
- Start Backend API on port 8005 (with hot reload)
- Start Frontend on port 8006 (with hot reload)

### 4. Access the Development Environment

Once services are running, access:

- **Frontend Dashboard**: http://localhost:8006
  - React app with real-time agent visualization
  - Human-in-the-loop interface
  - Live updates via SSE

- **Backend API**: http://localhost:8005
  - FastAPI REST endpoints
  - Health check: http://localhost:8005/

- **API Documentation**: http://localhost:8005/docs
  - Interactive Swagger UI
  - Test endpoints directly

- **PostgreSQL**: localhost:8007
  - Database connection for external tools
  - Connection string: `postgresql://cerina:cerina_password@localhost:8007/cerina_foundry`

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Or use Makefile
make logs
make logs-backend
make logs-frontend
make logs-db
```

### 6. Hot Reload Features

In development mode:
- **Backend**: Code changes in `backend/` automatically reload
- **Frontend**: Code changes in `frontend/` automatically reload
- **Database**: Persisted in Docker volume (survives restarts)

### 7. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Development Workflow

### Making Backend Changes

1. Edit files in `backend/`
2. Changes are automatically detected and reloaded
3. Check logs: `docker-compose logs -f backend`

### Making Frontend Changes

1. Edit files in `frontend/src/`
2. Changes are automatically detected and hot-reloaded
3. Check logs: `docker-compose logs -f frontend`

### Database Access

```bash
# Open PostgreSQL shell
docker-compose exec postgres psql -U cerina -d cerina_foundry

# Or use Makefile
make db-shell
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:8005/

# Create a protocol
curl -X POST http://localhost:8005/api/protocols/create \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Create an exposure hierarchy for agoraphobia"}'

# List protocols
curl http://localhost:8005/api/protocols
```

## Troubleshooting

### Port Already in Use

If you get port conflicts:
```bash
# Check what's using the port
lsof -i :8005
lsof -i :8006
lsof -i :8007

# Kill the process or change ports in docker-compose.yml
```

### Services Won't Start

```bash
# Check service status
docker-compose ps

# View error logs
docker-compose logs

# Rebuild services
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U cerina -d cerina_foundry -c "SELECT 1;"
```

### Backend Not Reloading

```bash
# Restart backend
docker-compose restart backend

# Or rebuild
docker-compose build backend
docker-compose up -d backend
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Clear node_modules and rebuild
docker-compose exec frontend rm -rf node_modules
docker-compose restart frontend
```

## Useful Commands

```bash
# Start services
make dev                    # Development mode
make up                     # Standard mode
make prod                   # Production mode

# View logs
make logs                   # All services
make logs-backend          # Backend only
make logs-frontend         # Frontend only
make logs-db               # Database only

# Restart
make restart               # All services
make restart-backend       # Backend only

# Database
make db-shell              # PostgreSQL shell
make db-backup             # Backup database
make db-reset              # Reset database (WARNING: deletes data)

# Status
make status                # Show service status
```

## Next Steps

1. Open http://localhost:8006 in your browser
2. Enter a query like "Create an exposure hierarchy for agoraphobia"
3. Watch the agents work in real-time!
4. Review and approve the generated protocol

## Development Tips

- Use the API docs at http://localhost:8005/docs to test endpoints
- Check logs frequently: `docker-compose logs -f`
- Database persists in Docker volumes - use `make db-reset` to start fresh
- Frontend hot reload works for most changes (may need refresh for some)
- Backend auto-reloads on Python file changes


