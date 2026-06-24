# Sequentum Bridge Dockerfile
# Build: docker build -f src/bridges/sequentum/Dockerfile -t nep-sequentum-bridge .
# Watches Redis queue for Sequentum tasks, calls Sequentum API on Windows host

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

CMD ["python", "-u", "bridge.py"]
