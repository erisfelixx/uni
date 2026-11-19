"""
Auth - сервер авторизації системи моніторингу.
Перевіряє логін і пароль користувача (база користувачів - SQLite, паролі - хеші bcrypt),
видає токен сесії (JWT у cookie) і відповідає nginx, чи можна пропустити запит до Grafana.

Схема роботи:
  браузер -> nginx -> (auth_request) /auth/verify -> 200: запит іде в Grafana з іменем користувача
                                                   -> 401: перенаправлення на сторінку входу /auth/login
"""
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import quote

import bcrypt
import jwt
from flask import Flask, Response, make_response, redirect, render_template_string, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest


# Налаштування з docker-compose через змінні середовища

DB_PATH = os.getenv("AUTH_DB_PATH", "/data/users.db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")       # секретний ключ для підпису токенів
JWT_TTL_HOURS = int(os.getenv("JWT_TTL_HOURS", "8"))     # скільки годин діє сесія
COOKIE_NAME = "auth_token"
MAX_FAILED_ATTEMPTS = 5        # після стількох невдалих спроб вхід блокується (5хв)
LOCK_MINUTES = 5               

# Ролі нашої системи -> ролі Grafana
GRAFANA_ROLES = {"admin": "Admin", "viewer": "Viewer"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [auth] %(message)s")
log = logging.getLogger()

app = Flask(__name__)


# Метрики Prometheus

LOGIN_ATTEMPTS = Counter(
    "auth_login_attempts_total",
    "Спроби входу в систему",
    ["result"],                # success / failure / locked
)
VERIFY_REQUESTS = Counter(
    "auth_verify_requests_total",
    "Перевірки доступу від nginx",
    ["result"],                # allowed / denied
)
USERS_TOTAL = Gauge(
    "auth_users_total",
    "Кількість зареєстрованих користувачів",
)


# Робота з базою користувачів (SQLite)

def db():
    """Нове з'єднання з SQLite на кожен запит (так безпечно для кількох потоків)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Пароль зберігається лише як хеш bcrypt (з випадковою "сіллю"), не у відкритому вигляді."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def init_db():
    """Створення таблиць і початкових користувачів (якщо база порожня)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
                created_at    TEXT NOT NULL,
                last_login    TEXT
            )""")
        # Журнал спроб входу (аудит + захист від підбору пароля)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT NOT NULL,
                success   INTEGER NOT NULL,
                ip        TEXT,
                ts        REAL NOT NULL
            )""")
        if conn.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
            defaults = [
                (os.getenv("ADMIN_USER", "admin"), os.getenv("ADMIN_PASSWORD", "admin123"), "admin"),
                (os.getenv("VIEWER_USER", "viewer"), os.getenv("VIEWER_PASSWORD", "viewer123"), "viewer"),
            ]
            for username, password, role in defaults:
                create_user(conn, username, password, role)
                log.info("Created default user %s (%s)", username, role)
    update_users_metric()


def create_user(conn, username, password, role):
    conn.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), role, datetime.now(timezone.utc).isoformat()),
    )


def get_user(username):
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def update_users_metric():
    with db() as conn:
        USERS_TOTAL.set(conn.execute("SELECT count(*) FROM users").fetchone()[0])


def is_locked(username):
    """Чи заблоковано вхід: забагато невдалих спроб за останні LOCK_MINUTES хвилин."""
    since = time.time() - LOCK_MINUTES * 60
    with db() as conn:
        failures = conn.execute(
            "SELECT count(*) FROM login_log WHERE username = ? AND success = 0 AND ts > ?",
            (username, since),
        ).fetchone()[0]
    return failures >= MAX_FAILED_ATTEMPTS


def log_attempt(username, success):
    with db() as conn:
        conn.execute(
            "INSERT INTO login_log (username, success, ip, ts) VALUES (?, ?, ?, ?)",
            (username, int(success), client_ip(), time.time()),
        )
        if success:
            conn.execute("UPDATE users SET last_login = ? WHERE username = ?",
                         (datetime.now(timezone.utc).isoformat(), username))


def client_ip():
    # Реальна IP-адреса клієнта передається від nginx у заголовку X-Real-IP
    return request.headers.get("X-Real-IP", request.remote_addr)


# Токени сесії (JWT)

def make_token(user):
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user():
    """Користувач з cookie: перевіряємо підпис і термін дії токена, а також що користувач ще існує."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:          # підроблений або прострочений токен
        return None
    return get_user(payload["sub"])        # None, якщо користувача вже видалили


def admin_required(view):
    """Декоратор: сторінка доступна лише адміністратору."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect("/auth/login?next=" + quote(request.path))
        if user["role"] != "admin":
            return Response("Доступ лише для адміністратора", status=403)
        return view(user, *args, **kwargs)
    return wrapper


def safe_next(url):
    """Захист від перенаправлення на чужий сайт: дозволяємо лише внутрішні адреси."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return "/"


# HTML-шаблони (вбудовані, щоб увесь сервіс був в одному файлі)

PAGE_STYLE = """
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #111217; color: #ccccdc;
         display: flex; justify-content: center; align-items: flex-start; padding-top: 8vh; margin: 0; }
  .card { background: #181b1f; border: 1px solid #2c3235; border-radius: 8px; padding: 32px 40px; min-width: 340px; }
  h1 { font-size: 22px; font-weight: 500; margin: 0 0 4px; }
  p.sub { color: #8e8e9e; margin: 0 0 24px; font-size: 14px; }
  label { display: block; font-size: 13px; margin: 14px 0 6px; }
  input, select { width: 100%; box-sizing: border-box; padding: 9px 10px; background: #111217; color: #ccccdc;
                  border: 1px solid #3a3f45; border-radius: 4px; font-size: 14px; }
  button { margin-top: 22px; width: 100%; padding: 10px; background: #3d71d9; color: white; border: none;
           border-radius: 4px; font-size: 15px; cursor: pointer; }
  button.small { width: auto; margin: 0; padding: 4px 10px; font-size: 13px; background: #a8323e; }
  .error { background: #4a1f24; color: #ffb3b8; padding: 9px 12px; border-radius: 4px; font-size: 14px; }
  .ok { background: #1f3d2a; color: #a3e4b8; padding: 9px 12px; border-radius: 4px; font-size: 14px; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; margin-top: 12px; }
  td, th { text-align: left; padding: 6px 10px; border-bottom: 1px solid #2c3235; }
  a { color: #6e9fff; }
</style>
"""

LOGIN_PAGE = PAGE_STYLE + """
<div class="card">
  <h1>Служба доставки</h1>
  <p class="sub">Система моніторингу роботи БД — вхід</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="post">
    <input type="hidden" name="next" value="{{ next }}">
    <label>Логін</label><input name="username" autofocus required>
    <label>Пароль</label><input name="password" type="password" required>
    <button type="submit">Увійти</button>
  </form>
</div>
"""

USERS_PAGE = PAGE_STYLE + """
<div class="card">
  <h1>Користувачі</h1>
  <p class="sub">Ви увійшли як <b>{{ me }}</b> · <a href="/">до дашбордів</a> · <a href="/auth/logout">вийти</a></p>
  {% if message %}<div class="{{ 'error' if is_error else 'ok' }}">{{ message }}</div>{% endif %}
  <table>
    <tr><th>Логін</th><th>Роль</th><th>Останній вхід</th><th></th></tr>
    {% for u in users %}
    <tr><td>{{ u.username }}</td><td>{{ u.role }}</td><td>{{ (u.last_login or '—')[:19] }}</td>
      <td>{% if u.username != me %}
        <form method="post" action="/auth/users/{{ u.username }}/delete" style="margin:0">
          <button class="small" type="submit">Видалити</button></form>{% endif %}</td></tr>
    {% endfor %}
  </table>
  <form method="post" action="/auth/users">
    <label>Новий логін</label><input name="username" required pattern="[A-Za-z0-9_.-]{3,32}">
    <label>Пароль (мін. 6 символів)</label><input name="password" type="password" required minlength="6">
    <label>Роль</label>
    <select name="role"><option value="viewer">viewer — лише перегляд</option><option value="admin">admin</option></select>
    <button type="submit">Додати користувача</button>
  </form>
</div>
"""


# Маршрути

@app.get("/auth/login")
def login_form():
    return render_template_string(LOGIN_PAGE, error=None, next=safe_next(request.args.get("next")))


@app.post("/auth/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    next_url = safe_next(request.form.get("next"))

    if is_locked(username):
        LOGIN_ATTEMPTS.labels(result="locked").inc()
        log.warning("Login blocked for %s from %s: too many failed attempts", username, client_ip())
        error = f"Забагато невдалих спроб. Спробуйте через {LOCK_MINUTES} хв."
        return render_template_string(LOGIN_PAGE, error=error, next=next_url), 429

    user = get_user(username)
    if user is None or not check_password(password, user["password_hash"]):
        log_attempt(username, success=False)
        LOGIN_ATTEMPTS.labels(result="failure").inc()
        log.warning("Failed login for %s from %s", username, client_ip())
        return render_template_string(LOGIN_PAGE, error="Невірний логін або пароль", next=next_url), 401

    log_attempt(username, success=True)
    LOGIN_ATTEMPTS.labels(result="success").inc()
    log.info("User %s (%s) logged in from %s", username, user["role"], client_ip())

    resp = make_response(redirect(next_url))
    # HttpOnly - токен недоступний JavaScript'у; SameSite=Lax - захист від CSRF
    resp.set_cookie(COOKIE_NAME, make_token(user), max_age=JWT_TTL_HOURS * 3600,
                    httponly=True, samesite="Lax")
    return resp


@app.get("/auth/logout")
def logout():
    user = current_user()
    if user:
        log.info("User %s logged out", user["username"])
    resp = make_response(redirect("/auth/login"))
    resp.delete_cookie(COOKIE_NAME)
    return resp


@app.get("/auth/verify")
def verify():
    """Викликається nginx (auth_request) перед КОЖНИМ запитом до Grafana.
    200 + заголовки з іменем і роллю -> пропустити; 401 -> на сторінку входу."""
    user = current_user()
    if user is None:
        VERIFY_REQUESTS.labels(result="denied").inc()
        return Response(status=401)
    VERIFY_REQUESTS.labels(result="allowed").inc()
    resp = Response(status=200)
    resp.headers["X-User"] = user["username"]
    resp.headers["X-Role"] = GRAFANA_ROLES[user["role"]]
    return resp


@app.get("/auth/login-redirect")
def login_redirect():
    """nginx перенаправляє сюди неавторизовані запити; X-Original-URI - адреса, яку відкривав користувач.
    Після входу користувача буде повернуто саме туди."""
    original = request.headers.get("X-Original-URI", "/")
    return redirect("/auth/login?next=" + quote(safe_next(original), safe=""))


@app.get("/auth/users")
@admin_required
def users_page(me, message=None, is_error=False):
    with db() as conn:
        users = conn.execute("SELECT username, role, last_login FROM users ORDER BY id").fetchall()
    return render_template_string(USERS_PAGE, users=users, me=me["username"], message=message, is_error=is_error)


@app.post("/auth/users")
@admin_required
def add_user(me):
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "viewer")
    if len(password) < 6 or role not in GRAFANA_ROLES or not username:
        return users_page.__wrapped__(me, "Некоректні дані користувача", True)
    try:
        with db() as conn:
            create_user(conn, username, password, role)
    except sqlite3.IntegrityError:
        return users_page.__wrapped__(me, f"Користувач {username} вже існує", True)
    update_users_metric()
    log.info("Admin %s created user %s (%s)", me["username"], username, role)
    return users_page.__wrapped__(me, f"Користувача {username} додано")


@app.post("/auth/users/<username>/delete")
@admin_required
def delete_user(me, username):
    if username == me["username"]:
        return users_page.__wrapped__(me, "Не можна видалити самого себе", True)
    with db() as conn:
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
    update_users_metric()
    log.info("Admin %s deleted user %s", me["username"], username)
    return users_page.__wrapped__(me, f"Користувача {username} видалено")


@app.get("/auth/health")
def health():
    return "ok"


@app.get("/metrics")
def metrics():
    """Метрики для Prometheus (доступні лише всередині мережі Docker, nginx їх назовні не віддає)."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)