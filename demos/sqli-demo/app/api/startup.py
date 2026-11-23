"""The startup line that says where the demo is reached from the host."""
import logging


class _AddressOnHost(logging.Filter):
    """Rewrites Uvicorn's "running on http://0.0.0.0:8000", the address inside the container."""

    def __init__(self, line: str) -> None:
        super().__init__()
        self.line = line

    def filter(self, record: logging.LogRecord) -> bool:
        if str(record.msg).startswith("Uvicorn running on"):
            record.msg, record.args = self.line, ()
            record.__dict__.pop("color_message", None)
        return True


def announce(name: str, public_url: str) -> None:
    """Makes Uvicorn's startup line name the demo and the address the host reaches it at.

    Args:
        name: The demo, such as `sqli-demo`.
        public_url: The address on the host, such as `http://127.0.0.1:8001`.
    """
    logger = logging.getLogger("uvicorn.error")
    if not any(isinstance(f, _AddressOnHost) for f in logger.filters):
        logger.addFilter(_AddressOnHost(f"Mithridates · {name} is ready → {public_url}/docs"))
