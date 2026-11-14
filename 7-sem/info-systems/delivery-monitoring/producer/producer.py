"""
Producer - генератор подій служби доставки.
Імітує роботу диспетчерської: створює нові замовлення і поступово переводить їх по статусах. Кожна подія надсилається в RabbitMQ.
"""
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika
from prometheus_client import Counter, Gauge, start_http_server


# Налаштування з docker-compose через змінні середовища

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASS = os.getenv("RABBIT_PASS", "guest")
EXCHANGE = "delivery"          # direct-обмінник
ROUTING_KEY = "order_events"   # ключ маршрутизації
QUEUE = "order_events"         # черга, яку слухає worker
METRICS_PORT = 8000            # порт, з якого Prometheus забирає метрики (/metrics)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [producer] %(message)s")
log = logging.getLogger()


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

# Порядок статусів ("життєвий цикл" замовлення)
NEXT_STATUS = {
    "created": "assigned",
    "assigned": "picked_up",
    "picked_up": "in_transit",
    "in_transit": "delivered",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


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
    ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=ROUTING_KEY,
        body=json.dumps(event, ensure_ascii=False),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    EVENTS_PUBLISHED.labels(event=event["event"], status=event["status"]).inc()
    log.info("Published %s order=%s status=%s", event["event"], event["order_id"][:8], event["status"])


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

    conn, ch = connect()
    # Активні замовлення: order_id -> {"status", "courier_id", "next_at"}
    active = {}

    while True:
        # 1) З імовірністю 60% кожну секунду з'являється нове замовлення
        if random.random() < 0.6:
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
                st["courier_id"] = random.choice(COURIERS)

            publish(ch, {
                "event": "status_changed",
                "order_id": order_id,
                "status": new_status,
                "courier_id": st["courier_id"],
                "ts": now_iso(),
            })

            if new_status in ("delivered", "canceled"):
                del active[order_id]          # замовлення завершене
            else:
                st["status"] = new_status
                st["next_at"] = time.time() + random.uniform(3, 15)

        ORDERS_IN_PROGRESS.set(len(active))

        # conn.sleep (не time.sleep!), щоб pika обробляв heartbeat під час паузи
        conn.sleep(1)


if __name__ == "__main__":
    main()