import logging
import sys
from rich.logging import RichHandler
from app.config import settings

def setup_logger(name: str = "legal_engine") -> logging.Logger:
    """
    Configures and returns a structured logger with rich console output.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # Use Rich for beautiful, colored terminal logs
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True
        )
        formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger to avoid duplicate entries
        logger.propagate = False

    return logger

logger = setup_logger()
