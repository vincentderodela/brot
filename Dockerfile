# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/New_York

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create necessary directories
RUN mkdir -p logs data/cache data/historical

# Create a non-root user for security
RUN useradd -m -u 1000 brotuser && \
    chown -R brotuser:brotuser /app

# Switch to non-root user
USER brotuser

# Health check to ensure bot is running
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c "import os; exit(0 if os.path.exists('logs/trades.json') else 1)"

# Default command
CMD ["python", "run_trading_bot.py"]

