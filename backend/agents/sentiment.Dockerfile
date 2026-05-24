# priv/backend/agents/sentiment.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    google-cloud-pubsub==1.11.1 \
    google-cloud-firestore==2.14.0 \
    firebase-admin==6.2.0 \
    textblob==0.17.1 \
    requests==2.31.0

COPY priv/backend/agents/base_agent.py .
COPY priv/backend/agents/sentiment_agent.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "sentiment_agent.py"]
