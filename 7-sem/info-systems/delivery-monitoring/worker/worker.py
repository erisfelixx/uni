"""
Worker (обробник подій).
Отримує події з RabbitMQ і записує їх у PostgreSQL:
 - order_created  -> нове замовлення в orders + запис в order_events
 - status_changed -> оновлення статусу в orders + запис в order_events
"""
import json
import logging
import os
import time

import pika
import psycopg


# Налаштування
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASS = os.getenv("RABBIT_PASS", "guest")
EXCHANGE = "delivery"
ROUTING_KEY = "order_events"
QUEUE = "order_events"

DB_DSN = os.getenv("DB_DSN", "postgresql://delivery:delivery@localhost:5432/delivery")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [worker] %(message)s")
log = logging.getLogger()


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
    with db.transaction():
        if ev["event"] == "order_created":
            db.execute(
                """INSERT INTO orders (id, customer, district, address, price, status, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO NOTHING""",
                (ev["order_id"], ev["customer"], ev["district"], ev["address"],
                 ev["price"], ev["status"], ev["ts"], ev["ts"]),
            )
        else:  # status_changed
            db.execute(
                """UPDATE orders
                   SET status = %s,
                       courier_id = %s,
                       updated_at = %s,
                       delivered_at = CASE WHEN %s = 'delivered' THEN %s ELSE delivered_at END
                   WHERE id = %s""",
                (ev["status"], ev["courier_id"], ev["ts"], ev["status"], ev["ts"], ev["order_id"]),
            )
        # Історія змін
        db.execute(
            "INSERT INTO order_events (order_id, status, courier_id, event_time) VALUES (%s, %s, %s, %s)",
            (ev["order_id"], ev["status"], ev.get("courier_id"), ev["ts"]),
        )


def main():
    db = connect_db()
    conn, ch = connect_rabbit()

    def on_message(channel, method, properties, body):
        try:
            ev = json.loads(body)
            save_event(db, ev)
            channel.basic_ack(delivery_tag=method.delivery_tag)  # підтверджуємо обробку
            log.info("Saved %s order=%s status=%s", ev["event"], ev["order_id"][:8], ev["status"])
        except Exception as e:
            # Помилка: відхиляємо повідомлення без повернення в чергу, щоб не зациклитись
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            log.error("Failed to process message: %s", e)

    ch.basic_consume(queue=QUEUE, on_message_callback=on_message)
    log.info("Waiting for messages...")
    ch.start_consuming()


if __name__ == "__main__":
    main()