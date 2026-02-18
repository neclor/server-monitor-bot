from pathlib import Path
import asyncio
import logging

from bot.bot import Bot

from configs import log_config


logger: logging.Logger = logging.getLogger(__name__)


def main() -> None:
    _create_log_file()

    logger.info("Start")

    bot: Bot = Bot()
    bot.start()
    asyncio.get_event_loop().run_forever()

    logger.info("Exit")


def _create_log_file() -> None:
    path: Path = Path(log_config.LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()


if __name__ == "__main__": main()
