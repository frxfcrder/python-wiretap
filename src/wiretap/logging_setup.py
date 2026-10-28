import json
import logging
from datetime import datetime

TRAFFIC_LOG_FILE = "traffic.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

traffic_logger = logging.getLogger("traffic")
traffic_logger.setLevel(logging.INFO)
traffic_logger.propagate = False
traffic_handler = logging.FileHandler(TRAFFIC_LOG_FILE, encoding="utf-8")
traffic_handler.setFormatter(logging.Formatter("%(message)s"))
traffic_logger.addHandler(traffic_handler)


def log_traffic(entry):
    entry["time"] = datetime.now().isoformat(timespec="milliseconds")
    traffic_logger.info(json.dumps(entry, ensure_ascii=False))


def write_intercept(ip, method, url, payload_size, payload):
    log_entry = {
        "event": "proxy-intercept",
        "ip": ip,
        "method": method,
        "path": url,
        "length": payload_size,
        "payload": payload[:2000],
    }
    log_traffic(log_entry)
