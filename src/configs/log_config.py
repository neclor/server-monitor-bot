import logging


LOG_LEVEL: int = logging.WARNING
LOG_FORMAT: str = "[%(levelname)s %(asctime)s] %(name)s: %(message)s"
DATE_FORMAT: str = "%d-%m-%Y %H:%M"
LOG_PATH: str = "logs/bot.log"

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
