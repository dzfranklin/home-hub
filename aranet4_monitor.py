import asyncio
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from aranet4.client import Aranet4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PORT = 8031
ADDRESS = "C9:3B:EC:53:D7:B9"
LOC = "entryway"

loop = asyncio.new_event_loop()
monitor: Aranet4 | None = None


async def read_readings():
    global monitor
    if monitor is None or not monitor.device.is_connected:
        if monitor is not None:
            try:
                await monitor.device.disconnect()
            except Exception:
                pass
        monitor = Aranet4(address=ADDRESS)
        await monitor.connect()
        log.info("Connected to Aranet4")
    return await monitor.current_readings(details=True)


def get_readings(max_retries: int = 3):
    global monitor
    for attempt in range(max_retries):
        try:
            return loop.run_until_complete(read_readings())
        except Exception as e:
            log.warning("Attempt %d failed: %s", attempt + 1, e)
            monitor = None
            if attempt == max_retries - 1:
                raise
            time.sleep(0.25)


def format_metrics(r) -> str:
    return f"""\
co2_ppm{{loc="{LOC}"}} {r.co2}
humidity_pct{{loc="{LOC}"}} {r.humidity}
pressure_hpa{{loc="{LOC}"}} {r.pressure}
temperature_c{{loc="{LOC}"}} {r.temperature}
aranet4_battery_pct{{loc="{LOC}"}} {r.battery}
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            reading = get_readings()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(format_metrics(reading).encode())
        except Exception as e:
            log.error("Failed to get readings: %s", e)
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"# Error: {e}\n".encode())

    def log_message(self, format, *args):
        pass  # suppress request logging


if __name__ == "__main__":
    log.info("Starting server on port %d", PORT)
    HTTPServer(("", PORT), Handler).serve_forever()
