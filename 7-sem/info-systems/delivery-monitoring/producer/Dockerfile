FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pika==1.3.2 prometheus-client==0.21.1
COPY producer.py .
# -u: виводити логи одразу
CMD ["python", "-u", "producer.py"]