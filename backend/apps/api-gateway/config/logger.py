import json
import logging
import sys
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self,record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level" : record.levelname,
            "service" : "api",
            "message" : record.getMessage(),
        }
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields"):
            log_payload.update(record.extra_fields)
        return json.dumps(log_payload)

def setup_logging(log_level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger.addHandler(handler)

logger = logging.getLogger("api")
