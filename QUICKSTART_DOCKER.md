# Quick Start with Docker

## Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

## 1. Setup Environment

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

## 2. Start Services

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f
```

## 3. Access Services

- **Frontend Dashboard**: http://localhost:8006
- **Backend API**: http://localhost:8005
- **API Documentation**: http://localhost:8005/docs
- **PostgreSQL**: localhost:8007

## 4. Verify Everything Works

```bash
# Check service status
docker-compose ps

# Test backend health
curl http://localhost:8005/

# View backend logs
docker-compose logs backend
```

## 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Common Commands

```bash
# View logs
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
make logs-db           # Database only

# Restart services
make restart           # All services
make restart-backend   # Backend only

# Database operations
make db-shell          # Open PostgreSQL shell
make db-backup         # Backup database
make db-reset          # Reset database (WARNING: deletes data)
```

## Development Mode

For development with hot reload:

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use make
make dev
```

## Production Mode

For production deployment:

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# Or use make
make prod
```

## Troubleshooting

### Port Already in Use
If ports 5432, 8000, or 5173 are already in use, modify `docker-compose.yml` to use different ports.

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U cerina -d cerina_foundry -c "SELECT 1;"
```

### Backend Won't Start
```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep OPENAI_API_KEY

# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend Issues
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

## Next Steps

1. Open http://localhost:8006 in your browser
2. Enter a query like "Create an exposure hierarchy for agoraphobia"
3. Watch the agents work in real-time!
4. Review and approve the generated protocol

For more details, see [DOCKER.md](./DOCKER.md).




