FROM python:3.11-slim

WORKDIR /app

COPY dashboard_web/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY dashboard_web /app

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "60", "app:app"]

