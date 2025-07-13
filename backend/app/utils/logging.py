import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "job_id": getattr(record, "job_id", "N/A"),
            "worker": "PodcastWorker",
        }
        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
