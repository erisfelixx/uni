# Система моніторингу роботи БД служби доставки

Проєкт з дисципліни «Інформаційні системи».

Система імітує роботу служби доставки: замовлення створюються, отримують кур'єра, проходять статуси до доставки або скасування, і кожна зміна записується в PostgreSQL. Робота з базою даних відстежується через метрики (Prometheus), логи (Loki) і трейси (Tempo), а результати відображаються в Grafana. Доступ до системи мають лише авторизовані користувачі.

Детальний опис архітектури, реалізації, тестування та знайдених дефектів наведено у звіті до проєкту.

## Архітектура

```
                 ┌──────────── вхід ────────────┐
Браузер ──► nginx :8088 ──перевірка──► auth (Flask + SQLite)
                 └──► Grafana ──► Prometheus, Loki, Tempo

producer ──► RabbitMQ ──► worker ──► PostgreSQL ◄── postgres-exporter

метрики (/metrics) ──► Prometheus ──► Alertmanager ──► alert-receiver
логи (stdout)      ──► Alloy ──► Loki
трейси (OTLP)      ──► Tempo
```

| Компонент | Технологія | Призначення |
|---|---|---|
| producer | Python 3.12, pika | генерує замовлення і зміни статусів, надсилає події в RabbitMQ |
| worker | Python 3.12, pika, psycopg | забирає події з черги і записує їх у БД |
| postgres | PostgreSQL 16 | база даних служби доставки |
| rabbitmq | RabbitMQ 4.0 | брокер повідомлень між producer і worker |
| postgres-exporter | v0.16.0 | метрики стану СУБД для Prometheus |
| prometheus | v2.55 | збір і зберігання метрик (TSDB), правила алертів |
| alertmanager | v0.27 | групування, придушення і розсилка сповіщень |
| alert-receiver | Python 3.12 | отримує сповіщення і записує їх у лог |
| loki + alloy | Loki 3.2, Alloy | збір і зберігання логів усіх контейнерів |
| tempo | Tempo 2.6 | зберігання трейсів (OpenTelemetry) |
| grafana | Grafana 11.2 | дашборд із 32 панелей, перегляд логів і трейсів |
| auth | Python 3.12, Flask, SQLite | сервер авторизації: вхід, ролі, керування користувачами |
| nginx | nginx 1.27 | єдина точка входу, перевіряє доступ перед кожним запитом |

## Запуск

Потрібні Docker Desktop (з Docker Compose) і Python 3 для тесту.

```bash
# запуск (перший раз — зі збиранням образів)
docker compose up -d --build

# стан контейнерів
docker compose ps

# перевірка працездатності (через 2–3 хв після запуску)
python3 tests/smoke_test.py

# зупинка (дані зберігаються)
docker compose down

# зупинка з видаленням усіх даних
docker compose down -v
```

## Адреси та облікові записи

| Інтерфейс | Адреса | Вхід |
|---|---|---|
| Система (дашборд, логи, трейси) | http://localhost:8088 | `admin` / `admin123`, `viewer` / `viewer123` |
| Керування користувачами | http://localhost:8088/auth/users | `admin` |
| RabbitMQ | http://localhost:15672 | `admin` / `admin` |
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| Alloy | http://localhost:12345 | — |

Grafana напряму недоступна: вона довіряє імені користувача, яке передає nginx, тому відкривається тільки через http://localhost:8088.

> Паролі та ключ `JWT_SECRET` у `docker-compose.yml` призначені лише для навчального середовища. Для реального використання їх треба змінити і винести в `.env`.

## Моніторинг

**Алерти** (`prometheus/alert_rules.yml`):

| Алерт | Умова | Важливість |
|---|---|---|
| ServiceDown | джерело метрик недоступне понад 30 с | critical |
| PostgresDown | БД не відповідає понад 30 с | critical |
| SlowDBQueries | p95 запитів до БД > 100 мс протягом 2 хв | warning |
| EventProcessingErrors | помилки запису подій за 5 хв | warning |
| RabbitMQQueueBacklog | у черзі понад 50 повідомлень протягом 1 хв | warning |
| OrdersWaitingForCourier | понад 10 замовлень чекають на кур'єра протягом 1 хв | warning |
| TooManyFailedLogins | понад 5 невдалих входів за 5 хв | warning |
| AllCouriersBusy | усі 10 кур'єрів зайняті понад 2 хв | info |

Коли спрацьовує PostgresDown, Alertmanager не надсилає алерти-наслідки (SlowDBQueries, EventProcessingErrors, RabbitMQQueueBacklog).

**Приклади запитів** (Grafana → Explore):

```
# PromQL — замовлення, що чекають на кур'єра
delivery_orders_by_status{status="created"}

# LogQL — логи про автоскасування завислих замовлень
{service="worker"} |= "Auto-canceled"

# TraceQL — повільні обробки подій
{ resource.service.name = "worker" && duration > 100ms }
```

У кожному рядку логу є `trace_id`, тож у Grafana з логу можна перейти до трейсу і навпаки.

## Тестування

`tests/smoke_test.py` (лише стандартна бібліотека Python) виконує 26 перевірок: інфраструктура, метрики й потік даних, логи/трейси/алерти, авторизація. У штатному режимі результат — 26/26. При будь-якому провалі скрипт завершується з кодом 1.

Сценарії збоїв для перевірки:

```bash
docker compose stop worker      # черга росте, ServiceDown; після start — черга обробляється без втрат
docker compose stop rabbitmq    # ServiceDown; producer і worker перезапускаються Docker і відновлюються після start
docker compose start worker rabbitmq
```

## Структура проєкту

```
delivery-monitoring/
├── docker-compose.yml             опис усіх 14 сервісів
├── db/init.sql                    схема БД і початкові дані
├── producer/                      генератор подій (producer.py, Dockerfile)
├── worker/                        обробник подій (worker.py, Dockerfile)
├── auth/                          сервер авторизації (app.py, Dockerfile)
├── alert-receiver/                отримувач сповіщень (receiver.py, Dockerfile)
├── nginx/default.conf             точка входу і перевірка доступу
├── prometheus/                    збір метрик (prometheus.yml) і правила алертів (alert_rules.yml)
├── alertmanager/alertmanager.yml  маршрутизація сповіщень
├── loki/loki-config.yaml          сховище логів
├── alloy/config.alloy             збір логів контейнерів
├── tempo/tempo.yaml               сховище трейсів
├── grafana/
│   ├── provisioning/              джерела даних і підключення дашбордів
│   └── dashboards/delivery.json   дашборд
└── tests/smoke_test.py            автоматичний тест
```

## Обмеження

Система навчальна, тому має свідомі спрощення:
- без HTTPS;
- паролі за замовчуванням у `docker-compose.yml`;
- службові інтерфейси (Prometheus, RabbitMQ, Alertmanager) доступні без входу;
- сповіщення лише записуються в лог (у `alertmanager.yml` є закоментований приклад надсилання на пошту).