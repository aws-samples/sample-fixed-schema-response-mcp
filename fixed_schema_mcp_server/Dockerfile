FROM python:3.12-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using pip (matching the AWS sample pattern)
RUN pip install --no-cache-dir fastmcp>=2.3.0 boto3>=1.28.0 jsonschema>=4.0.0 openai>=1.0.0 anthropic>=0.25.0

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for MCP server (streamable-http)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV VERSION=0.1.0
# Note: MCP_TRANSPORT and FASTMCP_STATELESS_HTTP are set via ECS task definition
# Health check - use /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the FastMCP server directly with python (matching AWS sample pattern)
CMD ["python", "fastmcp_server.py"]
