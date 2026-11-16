"""
Alert receiver — отримувач сповіщень від Alertmanager (webhook).
Приймає POST-запити з алертами і записує їх у лог. Логи потрапляють у Loki, тому всі сповіщення видно в Grafana (панель "Помилки та попередження").
"""
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 5001

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [alert-receiver] %(message)s")
log = logging.getLogger()


class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Alertmanager надсилає JSON зі списком алертів (стан firing або resolved)."""
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")

        for alert in payload.get("alerts", []):
            name = alert["labels"].get("alertname", "unknown")
            severity = alert["labels"].get("severity", "none")
            summary = alert.get("annotations", {}).get("summary", "")
            description = alert.get("annotations", {}).get("description", "")

            if alert.get("status") == "resolved":
                log.info("ALERT RESOLVED [%s] %s: %s", severity, name, summary)
            elif severity == "critical":
                log.error("ALERT FIRING [%s] %s: %s. %s", severity, name, summary, description)
            else:
                log.warning("ALERT FIRING [%s] %s: %s. %s", severity, name, summary, description)

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Перевірка, що сервіс живий: GET /health."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass  # вимикаємо стандартний лог кожного HTTP-запиту, щоб не засмічувати логи


if __name__ == "__main__":
    log.info("Alert receiver listening on port %s", PORT)
    HTTPServer(("0.0.0.0", PORT), AlertHandler).serve_forever()