FROM python:3.11-slim

WORKDIR /app

COPY services/graph_writer/requirements.txt /app/services/graph_writer/requirements.txt
RUN pip install --no-cache-dir -r /app/services/graph_writer/requirements.txt

COPY services/graph_writer /app/services/graph_writer

CMD ["python", "/app/services/graph_writer/main.py"]

