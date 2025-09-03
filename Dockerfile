# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY .env.example ./

# Install uv for fast dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Create non-root user
RUN useradd --create-home --shell /bin/bash alertprocessor
RUN chown -R alertprocessor:alertprocessor /app

# Create data and logs directories
RUN mkdir -p /app/data /app/logs
RUN chown -R alertprocessor:alertprocessor /app/data /app/logs

# Switch to non-root user
USER alertprocessor

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m src.main --test || exit 1

# Default command
CMD ["python", "-m", "src.main", "--daemon"]

# Expose port for potential web interface
EXPOSE 8080
