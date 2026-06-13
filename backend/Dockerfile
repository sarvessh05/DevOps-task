FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /workspace

# Set work directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /workspace/

# Default port exposed by fastapi
EXPOSE 8000

# Start command is overridden in docker-compose.yml for Celery worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
