import os
import logging
from pathlib import Path


LOG_LEVEL: int = logging.WARNING
LOG_FORMAT: str = "[%(levelname)s %(asctime)s] %(name)s: %(message)s"
DATE_FORMAT: str = "%d-%m-%Y %H:%M"
LOG_PATH: Path = Path(os.getenv("LOG_PATH", "logs/bot.log"))


LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
