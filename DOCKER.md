# Docker Deployment Guide

This guide explains how to build and run the AI GitHub Code Analyzer using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (usually included with Docker Desktop)
- OpenRouter API key (sign up at [openrouter.ai](https://openrouter.ai))

## Quick Start

### 1. Using Docker Compose (Recommended)

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <your-repo-url>
   cd agentic-code-exp
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit the .env file and add your OpenRouter API key
   # OPENROUTER_API_KEY=your_api_key_here
   ```

3. **Build and run the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   Open your browser and go to `http://localhost:8501`

### 2. Using Docker Commands Directly

1. **Build the Docker image**
   ```bash
   docker build -t ai-github-analyzer .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name ai-github-analyzer \
     -p 8501:8501 \
     -e OPENROUTER_API_KEY=your_api_key_here \
     -v $(pwd)/sample_output:/app/sample_output \
     -v $(pwd)/repos:/app/repos \
     ai-github-analyzer
   ```

## Configuration

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `OPENROUTER_API_KEY` | **Required** - Your OpenRouter API key | None |
| `DEFAULT_MODEL` | AI model to use | `mistralai/mixtral-8x7b-instruct` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CACHE_ENABLED` | Enable caching | `true` |
| `CACHE_TTL` | Cache time-to-live in seconds | `3600` |
| `MAX_FILES_DEFAULT` | Default maximum files to analyze | `100` |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | `1` |
| `ANALYSIS_TIMEOUT_MINUTES` | Analysis timeout in minutes | `30` |

### Volume Mounts

- `./sample_output:/app/sample_output` - Persistent storage for analysis reports
- `./repos:/app/repos` - Persistent storage for cloned repositories

## Docker Commands

### Build Commands
```bash
# Build the image
docker build -t ai-github-analyzer .

# Build with specific tag
docker build -t ai-github-analyzer:v1.0 .

# Build without cache
docker build --no-cache -t ai-github-analyzer .
```

### Run Commands
```bash
# Run in background
docker run -d --name ai-github-analyzer -p 8501:8501 ai-github-analyzer

# Run with environment file
docker run -d --name ai-github-analyzer -p 8501:8501 --env-file .env ai-github-analyzer

# Run with interactive terminal (for debugging)
docker run -it --name ai-github-analyzer -p 8501:8501 ai-github-analyzer bash
```

### Management Commands
```bash
# View logs
docker logs ai-github-analyzer

# Follow logs in real-time
docker logs -f ai-github-analyzer

# Stop the container
docker stop ai-github-analyzer

# Start the container
docker start ai-github-analyzer

# Remove the container
docker rm ai-github-analyzer

# Remove the image
docker rmi ai-github-analyzer
```

### Docker Compose Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8501
   netstat -tulpn | grep 8501
   
   # Use a different port
   docker run -p 8502:8501 ai-github-analyzer
   ```

2. **Permission denied errors**
   ```bash
   # On Linux/macOS, ensure proper permissions
   sudo chown -R $USER:$USER sample_output repos
   ```

3. **Container won't start**
   ```bash
   # Check container logs
   docker logs ai-github-analyzer
   
   # Run container interactively for debugging
   docker run -it ai-github-analyzer bash
   ```

4. **Out of memory errors**
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or add memory limit to docker run command
   docker run --memory=2g ai-github-analyzer
   ```

### Health Check

The container includes a health check that verifies the Streamlit application is running properly:

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' ai-github-analyzer

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' ai-github-analyzer
```

## Production Deployment

### Resource Recommendations

- **Minimum**: 512MB RAM, 0.5 CPU cores
- **Recommended**: 2GB RAM, 1 CPU core
- **Heavy usage**: 4GB RAM, 2 CPU cores

### Security Considerations

1. **Use secrets management** for API keys in production
2. **Run behind a reverse proxy** (nginx, traefik) for HTTPS
3. **Set up proper firewall rules**
4. **Regular security updates** of base images

### Example Production docker-compose.yml

```yaml
version: '3.8'
services:
  ai-github-analyzer:
    build: .
    restart: unless-stopped
    environment:
      - OPENROUTER_API_KEY_FILE=/run/secrets/openrouter_api_key
    secrets:
      - openrouter_api_key
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M

secrets:
  openrouter_api_key:
    external: true
```

## Multi-Architecture Builds

To build for multiple architectures (ARM64, AMD64):

```bash
# Create a builder
docker buildx create --name multiarch-builder --use

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t ai-github-analyzer:multiarch .
```

## Container Registry

### Push to Docker Hub
```bash
# Tag the image
docker tag ai-github-analyzer:latest yourusername/ai-github-analyzer:latest

# Push to Docker Hub
docker push yourusername/ai-github-analyzer:latest
```

### Pull from Registry
```bash
# Pull the image
docker pull yourusername/ai-github-analyzer:latest

# Run the pulled image
docker run -d -p 8501:8501 yourusername/ai-github-analyzer:latest
```
