import asyncio
import logging

from server_monitor_bot.server_monitor_bot import ServerMonitorBot


logger: logging.Logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Start")

    bot: ServerMonitorBot = ServerMonitorBot()
    bot.start()
    asyncio.get_event_loop().run_forever()

    logger.info("Exit")


if __name__ == "__main__": main()
