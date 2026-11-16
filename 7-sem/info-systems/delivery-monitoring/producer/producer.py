"""
Producer - генератор подій служби доставки.
Імітує роботу диспетчерської: створює нові замовлення і поступово переводить їх по статусах. Кожна подія надсилається в RabbitMQ.
"""
import json
import logging
import math
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika
from prometheus_client import Counter, Gauge, start_http_server
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# Налаштування з docker-compose через змінні середовища

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASS = os.getenv("RABBIT_PASS", "guest")
EXCHANGE = "delivery"          # direct-обмінник
ROUTING_KEY = "order_events"   # ключ маршрутизації
QUEUE = "order_events"         # черга, яку слухає worker
METRICS_PORT = 8000            # порт, з якого Prometheus забирає метрики (/metrics)
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")  # куди надсилати трейси (Tempo)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [producer] %(message)s")
log = logging.getLogger()
tracer = trace.get_tracer("producer")   # створює спани (кроки трейсу)


# Метрики Prometheus

EVENTS_PUBLISHED = Counter(
    "delivery_events_published_total",
    "Кількість подій, надісланих у RabbitMQ",
    ["event", "status"],
)
ORDERS_IN_PROGRESS = Gauge(
    "delivery_orders_in_progress",
    "Кількість незавершених замовлень у диспетчерській",
)

# Довідникові дані для генерації
CUSTOMERS = ["Іван", "Олена", "Петро", "Софія", "Максим", "Анна", "Богдан", "Катерина"]
DISTRICTS = ["Центр", "Поділ", "Оболонь", "Печерськ", "Троєщина", "Голосіїв"]
STREETS = ["Хрещатик", "Шевченка", "Франка", "Лесі Українки", "Сагайдачного"]
COURIERS = list(range(1, 11))  # id кур'єрів

# Інтенсивність замовлень змінюється хвилями ("години пік"):
# імовірність нового замовлення щосекунди коливається від 0.15 до 0.45 з періодом 10 хв
BASE_ORDER_RATE = 0.30
PEAK_AMPLITUDE = 0.15
PEAK_PERIOD = 600              # секунд

# Порядок статусів ("життєвий цикл" замовлення)
NEXT_STATUS = {
    "created": "assigned",
    "assigned": "picked_up",
    "picked_up": "in_transit",
    "in_transit": "delivered",
}


def setup_tracing(service_name):
    """Налаштування OpenTelemetry: спани збираються пачками й відправляються в Tempo по OTLP/HTTP."""
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT)))
    trace.set_tracer_provider(provider)


def trace_id_hex(span):
    """trace_id у звичному вигляді (32 hex-символи) — для логів, щоб зв'язати лог із трейсом."""
    return format(span.get_span_context().trace_id, "032x")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def order_probability():
    """Імовірність появи нового замовлення в поточну секунду (синусоїда навколо BASE_ORDER_RATE)."""
    return BASE_ORDER_RATE + PEAK_AMPLITUDE * math.sin(2 * math.pi * time.time() / PEAK_PERIOD)


def connect():
    """Підключення до RabbitMQ з повторними спробами (брокер може ще стартувати)."""
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    while True:
        try:
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            # Оголошуємо обмінник, чергу і зв'язок між ними (durable = переживуть перезапуск)
            ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
            ch.queue_declare(queue=QUEUE, durable=True)
            ch.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)
            log.info("Connected to RabbitMQ")
            return conn, ch
        except pika.exceptions.AMQPConnectionError:
            log.warning("RabbitMQ is not available, retry in 3 s...")
            time.sleep(3)


def publish(ch, event):
    """Надсилання події в RabbitMQ (delivery_mode=2 — повідомлення зберігається на диску)."""
    # Спан "publish" — початок трейсу; його контекст передається worker'у в заголовках повідомлення
    with tracer.start_as_current_span(f"publish {event['event']}", kind=trace.SpanKind.PRODUCER) as span:
        span.set_attribute("messaging.system", "rabbitmq")
        span.set_attribute("messaging.destination.name", EXCHANGE)
        span.set_attribute("order.id", event["order_id"])
        span.set_attribute("order.status", event["status"])

        headers = {}
        propagate.inject(headers)   # додає заголовок traceparent (id трейсу + id поточного спану)

        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=json.dumps(event, ensure_ascii=False),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2, headers=headers),
        )
        EVENTS_PUBLISHED.labels(event=event["event"], status=event["status"]).inc()
        log.info("Published %s order=%s status=%s trace_id=%s",
                 event["event"], event["order_id"][:8], event["status"], trace_id_hex(span))


def new_order():
    """Створення випадкового нового замовлення."""
    return {
        "event": "order_created",
        "order_id": str(uuid.uuid4()),
        "customer": random.choice(CUSTOMERS),
        "district": random.choice(DISTRICTS),
        "address": f"вул. {random.choice(STREETS)}, {random.randint(1, 150)}",
        "price": round(random.uniform(80, 1500), 2),
        "status": "created",
        "ts": now_iso(),
    }


def main():
    # HTTP-сервер з метриками у фоновому потоці: http://<host>:8000/metrics
    start_http_server(METRICS_PORT)
    log.info("Metrics available on port %s", METRICS_PORT)
    setup_tracing("producer")

    conn, ch = connect()
    # Активні замовлення: order_id -> {"status", "courier_id", "next_at"}
    active = {}
    # Вільні кур'єри: замовлення призначається лише вільному, після доставки кур'єр звільняється
    free_couriers = set(COURIERS)

    while True:
        # 1) Кожну секунду з певною імовірністю (залежить від "години пік") з'являється нове замовлення
        if random.random() < order_probability():
            order = new_order()
            publish(ch, order)
            active[order["order_id"]] = {
                "status": "created",
                "courier_id": None,
                "next_at": time.time() + random.uniform(2, 8),
            }

        # 2) Просуваємо по статусах ті замовлення, для яких настав час
        for order_id, st in list(active.items()):
            if time.time() < st["next_at"]:
                continue

            # ~5% замовлень скасовуються (до моменту, як кур'єр їх забрав)
            if st["status"] in ("created", "assigned") and random.random() < 0.05:
                new_status = "canceled"
            else:
                new_status = NEXT_STATUS[st["status"]]

            if new_status == "assigned":
                if not free_couriers:
                    # Усі кур'єри зайняті — замовлення чекає, перевіримо знову через 1 с
                    st["next_at"] = time.time() + 1
                    continue
                st["courier_id"] = random.choice(sorted(free_couriers))
                free_couriers.remove(st["courier_id"])

            publish(ch, {
                "event": "status_changed",
                "order_id": order_id,
                "status": new_status,
                "courier_id": st["courier_id"],
                "ts": now_iso(),
            })

            if new_status in ("delivered", "canceled"):
                if st["courier_id"] is not None:
                    free_couriers.add(st["courier_id"])   # кур'єр знову вільний
                del active[order_id]          # замовлення завершене
            else:
                st["status"] = new_status
                st["next_at"] = time.time() + random.uniform(3, 15)

        ORDERS_IN_PROGRESS.set(len(active))

        # conn.sleep (не time.sleep!), щоб pika обробляв heartbeat під час паузи
        conn.sleep(1)


if __name__ == "__main__":
    main()