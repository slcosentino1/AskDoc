import logging

_BUILTIN_LOG_RECORD_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)

_CELERY_LOG_RECORD_ATTRS = frozenset({"task_id", "task_name", "data"})

DEFAULT_LOG_FORMAT = "[%(levelname)s] %(name)s: %(message)s"
CELERY_LOG_FORMAT = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"


class ExtraFormatter(logging.Formatter):
    """Append structured ``extra`` fields to the log line."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _BUILTIN_LOG_RECORD_ATTRS
            and key not in _CELERY_LOG_RECORD_ATTRS
            and not key.startswith("_")
        }
        if not extras:
            return message

        extra_text = " ".join(f"{key}={value}" for key, value in sorted(extras.items()))
        return f"{message} {extra_text}"


def configure_logging(
    level: int = logging.INFO,
    *,
    log_format: str = DEFAULT_LOG_FORMAT,
) -> None:
    formatter = ExtraFormatter(log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    askdoc_logger = logging.getLogger("askdoc")
    askdoc_logger.handlers.clear()
    askdoc_logger.addHandler(handler)
    askdoc_logger.setLevel(level)
    askdoc_logger.propagate = False
