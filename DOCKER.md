# Docker Setup Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Development Setup

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **View logs:**
```bash
docker-compose logs -f
```

4. **Access services:**
- Frontend: http://localhost:8006
- Backend API: http://localhost:8005
- API Docs: http://localhost:8005/docs
- PostgreSQL: localhost:8007

### Development with Hot Reload

Use the dev override for hot reload:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This mounts your local code into containers for live updates.

## Services

### PostgreSQL Database
- **Port**: 8007 (external) -> 5432 (internal)
- **User**: cerina
- **Password**: cerina_password (change in production!)
- **Database**: cerina_foundry
- **Data**: Persisted in `postgres_data` volume

### Backend API
- **Port**: 8005
- **Health**: http://localhost:8005/
- **API Docs**: http://localhost:8005/docs
- **Environment**: Uses PostgreSQL from docker-compose

### Frontend
- **Port**: 8006
- **Dev Server**: Vite with hot reload
- **Production**: Nginx serving built files

## Production Deployment

### Build and Run Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

Create `.env` file with:
```env
OPENAI_API_KEY=your_key_here
POSTGRES_USER=cerina
POSTGRES_PASSWORD=strong_password_here
POSTGRES_DB=cerina_foundry
API_URL=https://your-domain.com
```

## Database Management

### Access PostgreSQL

```bash
# Using docker exec
docker-compose exec postgres psql -U cerina -d cerina_foundry

# Or using connection string
psql postgresql://cerina:cerina_password@localhost:5432/cerina_foundry
```

### Backup Database

```bash
docker-compose exec postgres pg_dump -U cerina cerina_foundry > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U cerina cerina_foundry < backup.sql
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volume
docker volume rm airbyte-common-handler_postgres_data

# Start again
docker-compose up -d
```

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes
```bash
docker-compose down -v
```

### Rebuild Services
```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache
```

### Execute Commands in Containers
```bash
# Backend shell
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python script.py

# Frontend shell
docker-compose exec frontend sh
```

## Troubleshooting

### Database Connection Issues

1. Check if PostgreSQL is healthy:
```bash
docker-compose ps
```

2. Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

3. Verify connection string in backend:
```bash
docker-compose exec backend env | grep DATABASE_URL
```

### Port Conflicts

If ports are already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change host port
```

### Permission Issues

If you encounter permission issues:
```bash
# Fix ownership
sudo chown -R $USER:$USER .
```

### Clear Everything and Start Fresh

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker-compose rm -f

# Remove volumes
docker volume prune

# Start fresh
docker-compose up -d --build
```

## Network Configuration

All services are on the `cerina-network` bridge network:
- Services can communicate using service names (e.g., `postgres`, `backend`)
- Backend connects to PostgreSQL using: `postgres:5432`
- Frontend can proxy to backend using: `backend:8000`

## Volume Persistence

- `postgres_data`: PostgreSQL database files
- `backend_data`: Backend application data (if any)

Data persists across container restarts. To reset, remove volumes:
```bash
docker-compose down -v
```




