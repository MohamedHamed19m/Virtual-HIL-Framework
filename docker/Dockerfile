# Virtual HIL Framework - Docker Image
# Multi-stage build using uv for dependency management

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Stage: Builder
FROM base AS builder

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Stage: Runtime
FROM base AS runtime

# Create non-root user
RUN useradd -m -u 1000 v hil && \
    mkdir -p /app/logs /app/reports /app/.pids && \
    chown -R vhil:vhil /app

# Copy installed dependencies from builder
COPY --from=builder --chown=vhil:vhil /app/.venv /app/.venv

# Copy application code
COPY --chown=vhil:vhil . .

# Set Python to use the venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Switch to non-root user
USER vhil

# Expose ports
# 8000 - REST API (if enabled)
# 9000 - CAN interface (if using virtual CAN)
EXPOSE 8000 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "-m", "ecu_simulation.battery_ecu"]

# Alternative entrypoint for running tests
# ENTRYPOINT ["uv", "run", "robot", "--pythonpath", "/app/libraries:/app/ecu_simulation", "--outputdir", "/app/reports", "tests/"]
