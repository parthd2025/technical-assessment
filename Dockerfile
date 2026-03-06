# Stage 1: Builder - separate stage for installing dependencies
FROM python:3.10-slim as builder

# Set working directory for the build stage
WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt .
# Install Python dependencies without cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal final image with only runtime dependencies
FROM python:3.10-slim

# Set working directory for the runtime stage
WORKDIR /app

# Copy installed packages from builder stage to avoid reinstalling
COPY --from=builder /usr/local /usr/local

# Disable Python output buffering and prevent .pyc file creation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application source code into the container
COPY src/ ./src/
# Copy environment configuration files if they exist
COPY .env* ./

# Create non-root user for security and set file ownership
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# Switch to non-root user for running the application
USER appuser

# Document that the application listens on port 8000
EXPOSE 8000

# Configure health check to monitor application availability
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Start the FastAPI application with Uvicorn server
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]