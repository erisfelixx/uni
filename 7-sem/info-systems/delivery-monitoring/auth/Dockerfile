FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3 bcrypt==4.2.1 PyJWT==2.10.1 gunicorn==23.0.0 prometheus-client==0.21.1
COPY app.py .
# gunicorn - production-сервер для Flask; 1 процес + 4 потоки (метрики Prometheus живуть в одному процесі)
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:app"]