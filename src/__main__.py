import asyncio
import logging

from src.bot import bot


logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s %(asctime)s] %(name)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M",
)

_logger: logging.Logger = logging.getLogger(__name__)


def main() -> None:
    _logger.info("Start")
    asyncio.run(bot.run())
    _logger.info("Exit")


if __name__ == "__main__": main()
