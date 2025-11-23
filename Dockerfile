FROM python:3.11-slim

WORKDIR /app

# Install gcc, postgres client, AND dos2unix to fix line ending issues automatically
RUN apt-get update && \
    apt-get install -y gcc postgresql-client dos2unix && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

# Fix line endings and make executable
RUN dos2unix start.sh && chmod +x start.sh

CMD ["./start.sh"]