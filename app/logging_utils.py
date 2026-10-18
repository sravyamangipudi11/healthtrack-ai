"""Append-only JSONL interaction log. Free-text notes are NOT logged (PHI risk); only a flag."""
import json, logging, time
from logging.handlers import RotatingFileHandler
from pathlib import Path


class InteractionLogger:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._log = logging.getLogger(f"interactions:{path}")
        self._log.setLevel(logging.INFO)
        self._log.propagate = False
        if not self._log.handlers:
            self._log.addHandler(RotatingFileHandler(path, maxBytes=5_000_000, backupCount=3))

    def record(self, **fields):
        self._log.info(json.dumps({"ts": time.time(), **fields}))

    def tail(self, n: int = 50) -> list[dict]:
        try:
            lines = Path(self.path).read_text().splitlines()[-n:]
        except FileNotFoundError:
            return []
        return [json.loads(l) for l in lines]
