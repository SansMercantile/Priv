# priv/backend/agents/strategist.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install GCP libraries
RUN pip install --no-cache-dir \
    google-cloud-pubsub==1.11.1 \
    google-cloud-firestore==2.14.0 \
    firebase-admin==6.2.0

# Copy agent code
COPY priv/backend/agents/base_agent.py .
COPY priv/backend/agents/strategist.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run agent
CMD ["python", "-u", "strategist.py"]
