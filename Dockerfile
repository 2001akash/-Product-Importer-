FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Set PYTHONPATH so Python can find app/ and tasks/
ENV PYTHONPATH=/app

# Create uploads directory
RUN mkdir -p /tmp/uploads

# Default command (can be overridden in docker-compose or render.yaml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]