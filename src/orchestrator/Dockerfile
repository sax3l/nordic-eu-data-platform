# Orchestrator Dockerfile
# Build: docker build -f src/orchestrator/Dockerfile -t nep-orchestrator .
# Used by docker-compose.full-stack.yml orchestrator service

FROM python:3.12-slim

WORKDIR /app

COPY requirements-orchestrator.txt .
RUN pip install --no-cache-dir -r requirements-orchestrator.txt

COPY src/orchestrator/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
