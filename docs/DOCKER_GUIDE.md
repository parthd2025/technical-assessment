# Docker Deployment Guide

## Overview
Both the backend API and frontend (comparison demo) are now containerized and can be started with a single command.

## Architecture

```
Docker Compose Setup:
├── Backend API (Port 8000) - FastAPI service
└── Frontend (Port 8501) - Streamlit comparison demo
```

## Quick Start

### Start Everything
```bash
docker-compose up -d
```

### Stop Everything
```bash
docker-compose down
```

### Rebuild and Start
```bash
docker-compose up -d --build
```

## Access URLs

- **Frontend (Comparison Demo)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs api

# Follow logs in real-time
docker-compose logs -f
```

## Check Status

```bash
# View running containers
docker ps

# Check health status
docker-compose ps
```

## Configuration

- **Backend**: Configured via `Dockerfile`
- **Frontend**: Configured via `Dockerfile.frontend`
- **Environment**: Variables in `.env` file
- **Streamlit Config**: `.streamlit/config.toml`

## Features

### Backend (Port 8000)
- RESTful API for clinical note processing
- Health check endpoint
- Automatic logging
- Resource limits configured

### Frontend (Port 8501)
- LLM vs Hybrid approach comparison
- PDF upload support
- Real-time token/time metrics
- Interactive demo interface

## Troubleshooting

### Port Conflicts
If ports 8000 or 8501 are in use:
```powershell
# Stop processes using the ports
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
Get-NetTCPConnection -LocalPort 8501 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

### Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Reset Everything
```bash
docker-compose down --volumes
docker-compose up -d --build
```

## Network

Both services run on the `clinical-network` Docker bridge network, allowing them to communicate internally if needed.

## Resource Limits

Each service is configured with:
- **CPU**: 1.0 cores max, 0.5 cores reserved
- **Memory**: 512MB max, 256MB reserved

Adjust in `docker-compose.yml` if needed.
