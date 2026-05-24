# priv/backend/agents/quantum.Dockerfile
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
    cirq==1.4.1 \
    qiskit==0.45.0 \
    numpy==1.26.0 \
    scipy==1.11.4

COPY priv/backend/agents/base_agent.py .
COPY priv/backend/agents/quantum_agent.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "quantum_agent.py"]
