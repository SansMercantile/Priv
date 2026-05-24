# priv/backend/agents/neuromorphic.Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    google-cloud-pubsub==1.11.1 \
    google-cloud-firestore==2.14.0 \
    firebase-admin==6.2.0 \
    nengo==3.1.0 \
    nengo-spa==2.2.0 \
    brian2==2.5.4 \
    norse==0.2.7 \
    numpy==1.26.0 \
    scipy==1.11.4

COPY priv/backend/agents/base_agent.py .
COPY priv/backend/agents/neuromorphic_agent.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "neuromorphic_agent.py"]
