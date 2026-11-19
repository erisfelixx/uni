"""
Smoke test - автоматична перевірка працездатності всієї системи однією командою.

Запуск (з кореня проєкту, коли система запущена через docker compose):
    python3 tests/smoke_test.py

Перевіряє: доступність сервісів, збір метрик, потік даних, логи, трейси, алерти й авторизацію.
Код завершення: 0 - усе гаразд, 1 - є провалені перевірки.
"""
import base64
import http.cookiejar
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# Адреси сервісів (порти з docker-compose.yml)

ENTRY_URL = os.getenv("ENTRY_URL", "http://localhost:8088")   # nginx - єдина точка входу
PROMETHEUS = "http://localhost:9090"
ALERTMANAGER = "http://localhost:9093"
LOKI = "http://localhost:3100"
TEMPO = "http://localhost:3200"
RABBITMQ_API = "http://localhost:15672/api"
RABBITMQ_AUTH = ("admin", "admin")

ADMIN = ("admin", os.getenv("ADMIN_PASSWORD", "admin123"))
VIEWER = ("viewer", os.getenv("VIEWER_PASSWORD", "viewer123"))

EXPECTED_JOBS = {"prometheus", "postgres", "rabbitmq", "producer", "worker", "loki",
                 "alloy", "tempo", "alertmanager", "auth"}
EXPECTED_ALERT_RULES = 8

TIMEOUT = 5  # секунд на один HTTP-запит


# Допоміжні функції

GREEN, RED, YELLOW, BOLD, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"
results = {"pass": 0, "fail": 0, "warn": 0}


def report(status, name, detail=""):
    """Вивести результат однієї перевірки: PASS / FAIL / WARN."""
    color, mark = {"pass": (GREEN, "✓"), "fail": (RED, "✗"), "warn": (YELLOW, "!")}[status]
    results[status] += 1
    print(f"  {color}{mark}{RESET} {name}" + (f"  — {detail}" if detail else ""))


def check(name, func):
    """Виконати перевірку: func повертає (status, detail); будь-яка помилка = FAIL."""
    try:
        status, detail = func()
    except Exception as e:  # сервіс недоступний, неочікувана відповідь тощо
        status, detail = "fail", f"{type(e).__name__}: {e}"
    report(status, name, detail)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Не переходити за перенаправленнями автоматично - нам треба бачити сам 302."""
    def redirect_request(self, *args, **kwargs):
        return None


def request(url, data=None, headers=None, opener=None, auth=None):
    """HTTP-запит; повертає (код, заголовки, тіло). Коди 3xx/4xx/5xx теж повертаються, а не кидають помилку."""
    headers = dict(headers or {})
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers)
    opener = opener or urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.headers, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode(errors="replace")


def prom_query(expr):
    """Миттєвий запит PromQL; повертає список (мітки, значення)."""
    _, _, body = request(f"{PROMETHEUS}/api/v1/query?" + urllib.parse.urlencode({"query": expr}))
    return [(r["metric"], float(r["value"][1])) for r in json.loads(body)["data"]["result"]]


def session():
    """Окремий "браузер" зі своїми cookie (для перевірок авторизації)."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(jar)), jar


def login(username, password):
    opener, jar = session()
    code, headers, _ = request(f"{ENTRY_URL}/auth/login",
                            data={"username": username, "password": password, "next": "/"}, opener=opener)
    return code, headers, opener, jar


# 1. Інфраструктура

def ready(url, expected="ready"):
    def run():
        code, _, body = request(url)
        ok = code == 200 and expected.lower() in body.lower()
        return ("pass" if ok else "fail"), f"HTTP {code}"
    return run


def loki_api():
    """Endpoint /ready у Loki (режим "все в одному") може повертати 503, хоча Loki працює,
    тому перевіряємо робочий API: список міток."""
    code, _, body = request(f"{LOKI}/loki/api/v1/labels")
    labels = json.loads(body).get("data", []) if code == 200 else []
    return ("pass" if code == 200 else "fail"), f"HTTP {code}, міток: {len(labels)}"


def rabbitmq_overview():
    code, _, body = request(f"{RABBITMQ_API}/overview", auth=RABBITMQ_AUTH)
    if code != 200:
        return "fail", f"HTTP {code}"
    return "pass", f"RabbitMQ {json.loads(body).get('rabbitmq_version', '?')}"


def grafana_port_closed():
    """Grafana не повинна бути доступна напряму (інакше можна обійти авторизацію)."""
    try:
        socket.create_connection(("localhost", 3000), timeout=2).close()
        return "fail", "порт 3000 відкритий — авторизацію можна обійти"
    except OSError:
        return "pass", "порт 3000 закритий"


# 2. Метрики

def all_targets_up():
    _, _, body = request(f"{PROMETHEUS}/api/v1/targets")
    targets = json.loads(body)["data"]["activeTargets"]
    up = {t["labels"]["job"] for t in targets if t["health"] == "up"}
    down = sorted(EXPECTED_JOBS - up)
    if down:
        return "fail", "недоступні: " + ", ".join(down)
    return "pass", f"усі {len(EXPECTED_JOBS)} джерел метрик UP"


def events_flowing():
    rate = sum(v for _, v in prom_query("sum(rate(delivery_events_processed_total[1m]))"))
    return ("pass" if rate > 0 else "fail"), f"{rate:.2f} подій/с записується в БД"


def queue_not_growing():
    ready_msgs = sum(v for _, v in prom_query("sum(rabbitmq_queue_messages_ready)"))
    return ("pass" if ready_msgs < 50 else "warn"), f"у черзі {ready_msgs:.0f} повідомлень"


def db_up():
    value = prom_query("pg_up")[0][1]
    return ("pass" if value == 1 else "fail"), "PostgreSQL відповідає" if value == 1 else "pg_up = 0"


def db_query_speed():
    rows = prom_query('histogram_quantile(0.95, sum by (le) '
                      '(rate(delivery_db_query_duration_seconds_bucket{operation!="stats"}[5m])))')
    p95_ms = rows[0][1] * 1000
    return ("pass" if p95_ms < 100 else "warn"), f"p95 = {p95_ms:.1f} мс (поріг 100 мс)"


def no_processing_errors():
    errors = sum(v for _, v in prom_query("sum(increase(delivery_events_failed_total[5m]))"))
    return ("pass" if errors == 0 else "warn"), f"{errors:.0f} помилок обробки за 5 хв"


def data_consistency():
    """Незавершених замовлень у БД не має бути значно більше, ніж реально активних у генераторі."""
    in_db = sum(v for _, v in prom_query(
        'sum(delivery_orders_by_status{status=~"created|assigned|picked_up|in_transit"})'))
    in_producer = sum(v for _, v in prom_query("delivery_orders_in_progress"))
    ok = in_db <= in_producer + 10
    return ("pass" if ok else "warn"), f"активних замовлень: у БД {in_db:.0f}, у генераторі {in_producer:.0f}"


# 3. Логи, трейси, алерти

def logs_collected():
    params = {"query": '{service="worker"}', "limit": 5,
              "start": str(int((time.time() - 300) * 1e9)), "end": str(int(time.time() * 1e9))}
    _, _, body = request(f"{LOKI}/loki/api/v1/query_range?" + urllib.parse.urlencode(params))
    lines = sum(len(s["values"]) for s in json.loads(body)["data"]["result"])
    return ("pass" if lines > 0 else "fail"), f"знайдено {lines} рядків логів worker за 5 хв"


def logs_have_trace_id():
    params = {"query": '{service="worker"} |= "trace_id="', "limit": 1,
              "start": str(int((time.time() - 300) * 1e9)), "end": str(int(time.time() * 1e9))}
    _, _, body = request(f"{LOKI}/loki/api/v1/query_range?" + urllib.parse.urlencode(params))
    found = any(s["values"] for s in json.loads(body)["data"]["result"])
    return ("pass" if found else "fail"), "логи містять trace_id (зв'язок лог → трейс)"


def traces_collected():
    params = {"q": '{resource.service.name="producer"}', "limit": 5,
              "start": int(time.time() - 900), "end": int(time.time())}
    _, _, body = request(f"{TEMPO}/api/search?" + urllib.parse.urlencode(params))
    traces = json.loads(body).get("traces", [])
    return ("pass" if traces else "fail"), f"знайдено {len(traces)} трейсів producer за 15 хв"


def service_graph():
    """Tempo рахує граф сервісів із трейсів: має бути зв'язок producer -> worker."""
    rows = prom_query('sum by (client, server) (traces_service_graph_request_total)')
    edges = {(m.get("client"), m.get("server")) for m, _ in rows}
    ok = ("producer", "worker") in edges
    return ("pass" if ok else "warn"), "producer → worker є в графі сервісів" if ok else f"зв'язки: {edges}"


def alert_rules_loaded():
    _, _, body = request(f"{PROMETHEUS}/api/v1/rules")
    rules = [r for g in json.loads(body)["data"]["groups"] for r in g["rules"] if r["type"] == "alerting"]
    ok = len(rules) >= EXPECTED_ALERT_RULES
    return ("pass" if ok else "fail"), f"завантажено {len(rules)} правил алертів"


def alertmanager_connected():
    _, _, body = request(f"{PROMETHEUS}/api/v1/alertmanagers")
    active = json.loads(body)["data"]["activeAlertmanagers"]
    return ("pass" if active else "fail"), f"Prometheus надсилає алерти в {len(active)} Alertmanager"


def firing_alerts():
    """Інформативно: які алерти зараз активні (у години пік AllCouriersBusy - це нормально)."""
    _, _, body = request(f"{PROMETHEUS}/api/v1/alerts")
    firing = [a["labels"]["alertname"] for a in json.loads(body)["data"]["alerts"] if a["state"] == "firing"]
    critical = [a["labels"]["alertname"] for a in json.loads(body)["data"]["alerts"]
                if a["state"] == "firing" and a["labels"].get("severity") == "critical"]
    if critical:
        return "fail", "критичні: " + ", ".join(critical)
    return ("warn" if firing else "pass"), ("активні: " + ", ".join(firing)) if firing else "активних алертів немає"


# 4. Авторизація

def anonymous_redirected():
    code, headers, _ = request(f"{ENTRY_URL}/")
    location = headers.get("Location", "")
    ok = code == 302 and "/auth/login" in location
    return ("pass" if ok else "fail"), f"HTTP {code} → {location or '—'}"


def forged_header_rejected():
    """Підроблений заголовок X-WEBAUTH-USER без входу не повинен пускати в Grafana."""
    code, headers, _ = request(f"{ENTRY_URL}/api/user", headers={"X-WEBAUTH-USER": "admin"})
    ok = code in (302, 401)
    return ("pass" if ok else "fail"), f"HTTP {code}"


def wrong_password_rejected():
    # Неіснуючий користувач, щоб тест не блокував справжні акаунти
    code, _, _, _ = login("smoke-test-nobody", "wrong-password")
    return ("pass" if code in (401, 429) else "fail"), f"HTTP {code}"


def admin_login_works():
    code, headers, opener, jar = login(*ADMIN)
    has_cookie = any(c.name == "auth_token" for c in jar)
    if code != 302 or not has_cookie:
        return "fail", f"HTTP {code}, cookie: {has_cookie}"
    cookie_flags = headers.get("Set-Cookie", "")
    if "HttpOnly" not in cookie_flags:
        return "warn", "cookie без HttpOnly"
    code, _, body = request(f"{ENTRY_URL}/api/user", opener=opener)
    user = json.loads(body) if code == 200 else {}
    ok = code == 200 and user.get("login") == "admin"
    return ("pass" if ok else "fail"), f"Grafana бачить користувача: {user.get('login', '—')}"


def viewer_restricted():
    code, _, opener, _ = login(*VIEWER)
    if code != 302:
        return "fail", f"вхід viewer: HTTP {code}"
    code_users, _, _ = request(f"{ENTRY_URL}/auth/users", opener=opener)
    code_role, _, body = request(f"{ENTRY_URL}/api/user/orgs", opener=opener)
    role = json.loads(body)[0]["role"] if code_role == 200 else "—"
    ok = code_users == 403 and role == "Viewer"
    return ("pass" if ok else "fail"), f"сторінка користувачів: HTTP {code_users}, роль у Grafana: {role}"


def logout_works():
    _, _, opener, _ = login(*ADMIN)
    request(f"{ENTRY_URL}/auth/logout", opener=opener)
    code, _, _ = request(f"{ENTRY_URL}/api/user", opener=opener)
    return ("pass" if code == 302 else "fail"), f"після виходу: HTTP {code}"


# Запуск

SECTIONS = [
    ("Інфраструктура", [
        ("Prometheus готовий", ready(f"{PROMETHEUS}/-/ready")),
        ("Alertmanager готовий", ready(f"{ALERTMANAGER}/-/ready", "ok")),
        ("Loki відповідає", loki_api),
        ("Tempo відповідає", ready(f"{TEMPO}/api/echo", "echo")),
        ("RabbitMQ відповідає", rabbitmq_overview),
        ("Grafana закрита для прямого доступу", grafana_port_closed),
    ]),
    ("Метрики і потік даних", [
        ("Усі джерела метрик доступні", all_targets_up),
        ("PostgreSQL працює", db_up),
        ("Події обробляються", events_flowing),
        ("Черга не накопичується", queue_not_growing),
        ("Швидкість запитів до БД", db_query_speed),
        ("Немає помилок обробки", no_processing_errors),
        ("Цілісність даних (немає завислих замовлень)", data_consistency),
    ]),
    ("Логи, трейси, алерти", [
        ("Логи збираються в Loki", logs_collected),
        ("Логи пов'язані з трейсами", logs_have_trace_id),
        ("Трейси збираються в Tempo", traces_collected),
        ("Граф сервісів будується", service_graph),
        ("Правила алертів завантажені", alert_rules_loaded),
        ("Prometheus підключений до Alertmanager", alertmanager_connected),
        ("Активні алерти", firing_alerts),
    ]),
    ("Авторизація", [
        ("Без входу — перенаправлення на сторінку входу", anonymous_redirected),
        ("Підроблений заголовок не пускає", forged_header_rejected),
        ("Невірний пароль відхиляється", wrong_password_rejected),
        ("Вхід admin працює", admin_login_works),
        ("Viewer має обмежені права", viewer_restricted),
        ("Вихід закриває доступ", logout_works),
    ]),
]


def main():
    print(f"{BOLD}Smoke test: система моніторингу служби доставки{RESET}  ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    for title, checks in SECTIONS:
        print(f"\n{BOLD}{title}{RESET}")
        for name, func in checks:
            check(name, func)

    total = sum(results.values())
    color = RED if results["fail"] else GREEN
    print(f"\n{BOLD}Підсумок:{RESET} {color}{results['pass']}/{total} пройдено{RESET}, "
          f"{results['warn']} попереджень, {results['fail']} провалено")
    sys.exit(1 if results["fail"] else 0)


if __name__ == "__main__":
    main()