"""
Worker (обробник подій).
Отримує події з RabbitMQ і записує їх у PostgreSQL:
 - order_created  -> нове замовлення в orders + запис в order_events
 - status_changed -> оновлення статусу в orders + запис в order_events
Додатково віддає метрики роботи з БД для Prometheus і трейси для Tempo.
"""
import json
import logging
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime

import pika
import psycopg
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode


# Налаштування
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASS = os.getenv("RABBIT_PASS", "guest")
EXCHANGE = "delivery"
ROUTING_KEY = "order_events"
QUEUE = "order_events"

DB_DSN = os.getenv("DB_DSN", "postgresql://delivery:delivery@localhost:5432/delivery")
METRICS_PORT = 8000            # порт для Prometheus (/metrics)
STATS_INTERVAL = 10            # як часто (с) рахувати статистику по таблицях
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")  # куди надсилати трейси (Tempo)

ALL_STATUSES = ["created", "assigned", "picked_up", "in_transit", "delivered", "canceled"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [worker] %(message)s")
log = logging.getLogger()
tracer = trace.get_tracer("worker")     # створює спани (кроки трейсу)


# Метрики Prometheus
EVENTS_PROCESSED = Counter(
    "delivery_events_processed_total",
    "Кількість подій, успішно записаних у БД",
    ["event", "status"],
)
EVENTS_FAILED = Counter(
    "delivery_events_failed_total",
    "Кількість подій, які не вдалося обробити",
)
DB_QUERY_DURATION = Histogram(
    "delivery_db_query_duration_seconds",
    "Тривалість операцій з БД",
    ["operation"],             # insert_order / update_status / insert_event / stats
)
DELIVERY_DURATION = Histogram(
    "delivery_order_duration_seconds",
    "Час від створення до доставки замовлення",
    buckets=[10, 20, 30, 45, 60, 90, 120, 180, 300],
)
REVENUE = Counter(
    "delivery_revenue_total",
    "Сума вартості доставлених замовлень, грн",
)
ORDERS_BY_STATUS = Gauge(
    "delivery_orders_by_status",
    "Кількість замовлень у БД за статусами",
    ["status"],
)
COURIERS_BUSY = Gauge(
    "delivery_couriers_busy",
    "Кількість кур'єрів, які зараз виконують замовлення",
)


def setup_tracing(service_name):
    """Налаштування OpenTelemetry: спани збираються пачками й відправляються в Tempo по OTLP/HTTP."""
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT)))
    trace.set_tracer_provider(provider)


def trace_id_hex(span):
    """trace_id у звичному вигляді (32 hex-символи) — для логів, щоб зв'язати лог із трейсом."""
    return format(span.get_span_context().trace_id, "032x")


@contextmanager
def db_operation(operation, statement):
    """Обгортка для операції з БД: одночасно спан у трейсі (Tempo) і замір тривалості (Prometheus)."""
    with tracer.start_as_current_span(f"db {operation}", kind=trace.SpanKind.CLIENT) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", operation)
        span.set_attribute("db.statement", statement)
        with DB_QUERY_DURATION.labels(operation=operation).time():
            yield


def connect_db():
    """Підключення до PostgreSQL з повторними спробами."""
    while True:
        try:
            conn = psycopg.connect(DB_DSN, autocommit=True)
            log.info("Connected to PostgreSQL")
            return conn
        except psycopg.OperationalError:
            log.warning("PostgreSQL is not available, retry in 3 s...")
            time.sleep(3)


def connect_rabbit():
    """Підключення до RabbitMQ з повторними спробами."""
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    while True:
        try:
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
            ch.queue_declare(queue=QUEUE, durable=True)
            ch.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
            ch.basic_qos(prefetch_count=10)  # не більше 10 непідтверджених повідомлень одночасно
            log.info("Connected to RabbitMQ")
            return conn, ch
        except pika.exceptions.AMQPConnectionError:
            log.warning("RabbitMQ is not available, retry in 3 s...")
            time.sleep(3)


def save_event(db, ev):
    """Запис події в БД. Одна транзакція - або все записано, або нічого."""
    with tracer.start_as_current_span("db transaction", kind=trace.SpanKind.CLIENT), db.transaction():
        if ev["event"] == "order_created":
            with db_operation("insert_order", "INSERT INTO orders ... ON CONFLICT DO NOTHING"):
                db.execute(
                    """INSERT INTO orders (id, customer, district, address, price, status, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING""",
                    (ev["order_id"], ev["customer"], ev["district"], ev["address"],
                     ev["price"], ev["status"], ev["ts"], ev["ts"]),
                )
        else:  # status_changed
            with db_operation("update_status", "UPDATE orders SET status ... RETURNING price, created_at"):
                row = db.execute(
                    """UPDATE orders
                       SET status = %s,
                           courier_id = %s,
                           updated_at = %s,
                           delivered_at = CASE WHEN %s = 'delivered' THEN %s ELSE delivered_at END
                       WHERE id = %s
                       RETURNING price, created_at""",
                    (ev["status"], ev["courier_id"], ev["ts"], ev["status"], ev["ts"], ev["order_id"]),
                ).fetchone()
            # Бізнес-метрики для доставлених замовлень
            if ev["status"] == "delivered" and row:
                price, created_at = row
                duration = (datetime.fromisoformat(ev["ts"]) - created_at).total_seconds()
                DELIVERY_DURATION.observe(duration)
                REVENUE.inc(float(price))
        # Історія змін
        with db_operation("insert_event", "INSERT INTO order_events ..."):
            db.execute(
                "INSERT INTO order_events (order_id, status, courier_id, event_time) VALUES (%s, %s, %s, %s)",
                (ev["order_id"], ev["status"], ev.get("courier_id"), ev["ts"]),
            )


def collect_db_stats():
    """Фоновий потік: кожні STATS_INTERVAL секунд рахує стан замовлень у БД.
    Має власне з'єднання, бо одне з'єднання не можна використовувати з двох потоків."""
    db = connect_db()
    while True:
        try:
            with db_operation("stats", "SELECT status, count(*) FROM orders GROUP BY status"):
                counts = dict(db.execute("SELECT status, count(*) FROM orders GROUP BY status").fetchall())
                busy = db.execute(
                    """SELECT count(DISTINCT courier_id) FROM orders
                       WHERE status IN ('assigned', 'picked_up', 'in_transit')"""
                ).fetchone()[0]
            for status in ALL_STATUSES:
                ORDERS_BY_STATUS.labels(status=status).set(counts.get(status, 0))
            COURIERS_BUSY.set(busy)
        except psycopg.Error as e:
            log.error("Stats query failed: %s", e)
            db = connect_db()
        time.sleep(STATS_INTERVAL)


def main():
    # HTTP-сервер з метриками у фоновому потоці: http://<host>:8000/metrics
    start_http_server(METRICS_PORT)
    log.info("Metrics available on port %s", METRICS_PORT)
    setup_tracing("worker")
    threading.Thread(target=collect_db_stats, daemon=True).start()

    db = connect_db()
    conn, ch = connect_rabbit()

    def on_message(channel, method, properties, body):
        # Відновлюємо контекст трейсу з заголовків повідомлення -> спан worker'а стає продовженням трейсу producer'а
        parent_ctx = propagate.extract(properties.headers or {})
        with tracer.start_as_current_span("process order_event", context=parent_ctx,
                                          kind=trace.SpanKind.CONSUMER) as span:
            try:
                ev = json.loads(body)
                span.set_attribute("order.id", ev["order_id"])
                span.set_attribute("order.status", ev["status"])
                save_event(db, ev)
                channel.basic_ack(delivery_tag=method.delivery_tag)  # підтверджуємо обробку
                EVENTS_PROCESSED.labels(event=ev["event"], status=ev["status"]).inc()
                log.info("Saved %s order=%s status=%s trace_id=%s",
                         ev["event"], ev["order_id"][:8], ev["status"], trace_id_hex(span))
            except Exception as e:
                # Помилка: відхиляємо повідомлення без повернення в чергу, щоб не зациклитись
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                EVENTS_FAILED.inc()
                span.record_exception(e)                 # помилка буде видна в трейсі
                span.set_status(Status(StatusCode.ERROR))
                log.error("Failed to process message: %s trace_id=%s", e, trace_id_hex(span))

    ch.basic_consume(queue=QUEUE, on_message_callback=on_message)
    log.info("Waiting for messages...")
    ch.start_consuming()


if __name__ == "__main__":
    main()