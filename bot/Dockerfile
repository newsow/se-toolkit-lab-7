FROM python:3.11-slim

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Sync dependencies (uv.lock is optional, uv sync works without it)
RUN uv sync --frozen || uv sync

# Copy the rest of the bot code
COPY . .

# Set entrypoint
ENTRYPOINT ["uv", "run", "bot.py"]
