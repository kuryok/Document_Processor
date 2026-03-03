import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "event": record.getMessage(),
        }
        custom_kwargs = getattr(record, "custom_kwargs", None)
        if isinstance(custom_kwargs, dict):
            log_obj.update(custom_kwargs)
        return json.dumps(log_obj)


class StructuredLogger:
    """A wrapper around standard logger to emit JSON structured logs."""

    def __init__(self, name: str, level: str = "INFO", log_file: Optional[str] = None, format: str = "json"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        handlers: list[logging.Handler] = []
        if log_file:
            path = Path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(str(path), encoding="utf-8"))

        # Always output to console
        handlers.append(logging.StreamHandler())

        for handler in handlers:
            if format.lower() == "json":
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(handler)

    def _log(self, level_func: Any, event: str, **kwargs: Any) -> None:
        extra = {"custom_kwargs": kwargs} if kwargs else {}
        level_func(event, extra=extra)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log(self.logger.info, event, **kwargs)

    def warn(self, event: str, **kwargs: Any) -> None:
        self._log(self.logger.warning, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log(self.logger.error, event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log(self.logger.debug, event, **kwargs)
