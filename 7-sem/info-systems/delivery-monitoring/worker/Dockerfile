FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pika==1.3.2 "psycopg[binary]==3.2.3" prometheus-client==0.21.1
COPY worker.py .
CMD ["python", "-u", "worker.py"]