FROM python:3.11-slim

WORKDIR /app

COPY services/sync_worker/requirements.txt /app/services/sync_worker/requirements.txt
RUN pip install --no-cache-dir -r /app/services/sync_worker/requirements.txt

COPY services/sync_worker /app/services/sync_worker

CMD ["python", "/app/services/sync_worker/main.py"]

