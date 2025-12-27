import asyncio
import logging
from telethon import TelegramClient, events
from telethon.types import Message
from telethon.events import NewMessage
import subprocess

from configs import api_keys, log_config
from modules import server_manager as sm


logger: logging.Logger = logging.getLogger(__name__)


class ServerBot:
    RETRY_DEALY: int = 60
    STATUS_UPDATE_DELAY: int = 10 * 60
    TELEGRAM_MESSAGE_LIMIT: int = 512
    MESSAGE_LIFETIME: int = 30


    def __init__(self) -> None:
        COMMANDS: dict = {
            r"(?i)(/)?sta(t|tu|tus)?": self._status,
            r"(?i)(/)?l(o|og|ogs)?": self._logs,
            r"(?i)(/)?u(p|pd|pda|pdat|pdate)?": self._update,
            r"(?i)(/)?r(e|es|est|esta|estar|estart)?": self._restart,
            r"(?i)(/)?/stop-bot": self._stop_bot,
            r"(?i)(/)?h(e|el|elp)?": self._help,
            r"(?i)(/)?v(e|er|ers|ersi|ersio|ersion)?": self._version,
        }

        self._client: TelegramClient = TelegramClient(api_keys.MY_SESSION_NAME, api_keys.API_ID, api_keys.API_HASH)
        self._is_running: bool = False

        self._status_message_ids: dict[int, int] = {}
        self._events: list[NewMessage.Event] = []

        for pattern, function in COMMANDS.items():
            self._client.on(events.NewMessage(chats=api_keys.USERS, from_users=api_keys.USERS, pattern=pattern))(function)


    def start(self) -> None:
        self._is_running = True
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        loop.create_task(self._connect())
        loop.create_task(self._update_status())


    async def _connect(self) -> None:
        while self._is_running:
            try:
                async with self._client:
                    logger.info("Connected successfully")
                    await self._client.disconnected
                    if not self._is_running: return
                    logger.warning(f"Connection lost")
            except Exception: pass

            await asyncio.sleep(self.RETRY_DEALY)


    async def _update_status(self) -> None:
        while self._is_running:
            if not self._client.is_connected():
                await asyncio.sleep(1)
                continue

            await self._delete_status_messages()

            for user in api_keys.USERS:
                try:
                    status_message = await self._client.send_message(user, sm.get_status())
                    self._status_message_ids[user] = status_message.id
                except Exception as e:
                    logger.warning(f"Error updating status: {e}")

            await asyncio.sleep(self.STATUS_UPDATE_DELAY)


    async def _status(self, event: NewMessage.Event) -> None:
        if user := event.sender_id in self._status_message_ids:
            try:
                await self._client.delete_messages(user, self._status_message_ids[user])
            except Exception as e:
                logger.warning(f"Deleting message error: {e}")

        try:
            self._status_message_ids[user] = event.message.id
            await event.edit(sm.get_status())
        except Exception as e:
            logger.warning(f"Editing message error: {e}")


    async def _logs(self, event: NewMessage.Event) -> None:
        logs: str = ""
        try:
            with open(log_config.LOG_PATH, "r") as log_file:
                logs = log_file.read()
                if len(logs) > self.TELEGRAM_MESSAGE_LIMIT: logs = logs[-self.TELEGRAM_MESSAGE_LIMIT:]
            await event.edit(log_config.LOG_PATH + ":\n" + logs)
        except Exception as e:
            logger.error(f"Logs sending error: {e}")
            try: await event.edit(f"Logs sending error: {e}")
            except Exception: pass

        await self._queue_delete_event(event)


    async def _update(self, event: NewMessage.Event) -> None:
        try:
            sm.git_pull()
            await event.edit("Update completed")
        except Exception as e:
            logger.error(f"Update error: {e}")
            try: await event.edit(f"Update error: {e}")
            except Exception: pass

        await self._queue_delete_event(event)


    async def _restart(self, event: NewMessage.Event) -> None:
        await self._delete_events()
        await self._delete_status_messages()

        try:
            sm.terminate_service()
        except Exception as e:
            logger.error(f"Service termination error: {e}")
            try: await event.edit(f"Service termination error: {e}")
            except Exception: pass

        await self._queue_delete_event(event)


    async def _stop_bot(self, event: NewMessage.Event) -> None:
        self._is_running = False

        await self._delete_events()
        await self._delete_status_messages()

        try: await event.edit(f"Bot has been stopped")
        except Exception as e:
            logger.warning(f"Editing message error: {e}")

        self._client.disconnect()
        logger.info("Bot has been stopped")


    async def _help(self, event: NewMessage.Event) -> None:
        try:
            await event.edit("""```
    Commands:
        status      Show status
        logs        Show logs
        update      Update bot
        restart     Restart bot
        /stop-bot   Stop bot
        help        Show help
        version     Show version
```"""
            )
        except Exception as e:
            logger.warning(f"Editing message error: {e}")

        await self._queue_delete_event(event)


    async def _version(self, event: NewMessage.Event) -> None:
        await event.edit("Server Status Bot v2.0.0 neclor")
        await self._queue_delete_event(event)


    async def _queue_delete_event(self, event: NewMessage.Event) -> None:
        self._events.append(event)
        await asyncio.sleep(self.MESSAGE_LIFETIME)

        try:
            await event.delete()
        except Exception as e:
            logger.warning(f"Deleting message error: {e}")

        if event in self._events: self._events.remove(event)


    async def _delete_events(self) -> None:
        for event in self._events:
            try:
                await event.delete()
            except Exception as e:
                logger.warning(f"Deleting message error: {e}")
        self._events = []


    async def _delete_status_messages(self) -> None:
        for user, id in self._status_message_ids.items():
            try:
                await self._client.delete_messages(user, id)
                del self._status_message_ids[user]
            except Exception as e:
                logger.warning(f"Deleting message error: {e}")
