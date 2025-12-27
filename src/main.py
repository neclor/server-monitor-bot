import asyncio
import logging

from configs import log_config
from server_bot.server_bot import ServerBot


logging.basicConfig(
    level=logging.INFO,
    format=log_config.LOG_FORMAT,
    datefmt=log_config.DATE_FORMAT,
    handlers=[logging.FileHandler(log_config.LOG_PATH), logging.StreamHandler()]
)
logger: logging.Logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Start")

    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    bot: ServerBot = ServerBot()
    bot.start()

    loop.run_forever()


if __name__ == "__main__": main()
