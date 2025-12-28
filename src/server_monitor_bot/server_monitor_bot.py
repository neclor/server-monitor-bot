import asyncio
import logging
from typing import cast
from telethon import TelegramClient
from telethon.events import NewMessage
from telethon.custom import Message

from configs import api_keys, log_config
from modules import server_manager as sm


logger: logging.Logger = logging.getLogger(__name__)


class ServerMonitorBot:
    RETRY_DEALY: int = 60
    STATUS_UPDATE_DELAY: int = 60 * 10
    TELEGRAM_MESSAGE_LIMIT: int = 2048
    MESSAGE_LIFETIME: int = 30


    def __init__(self) -> None:
        COMMANDS: dict[str, object] = {
            r"(?i)^(/?status)$": self._status,
            r"(?i)^(/?logs)$": self._logs,
            r"(?i)^(/?clean)$": self._clean,
            r"(?i)^(/?update)$": self._update,
            r"(?i)^(/?restart)$": self._restart,
            r"(?i)^(/stop-bot)$": self._stop_bot,
            r"(?i)^(/?help)$": self._help,
            r"(?i)^(/?version)$": self._version,
        }

        self._client: TelegramClient = TelegramClient(api_keys.MY_SESSION_NAME, api_keys.API_ID, api_keys.API_HASH)
        self._is_running: bool = False

        self._status_message_ids: dict[int, int] = {}
        self._message_ids: dict[int, set[int]] = {}

        for pattern, function in COMMANDS.items():
            self._client.on(NewMessage(chats=api_keys.USERS, from_users=api_keys.USERS, pattern=pattern))(function)


    def start(self) -> None:
        self._is_running = True
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        loop.create_task(self._connect())
        loop.create_task(self._autoupdate_status())


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


    async def _autoupdate_status(self) -> None:
        while self._is_running:
            if not self._client.is_connected():
                await asyncio.sleep(1)
                continue

            for chat_id in api_keys.USERS:
                self._remove_status_message_async(chat_id)

                if (message_id := await self._safe_send(chat_id, sm.get_status() + "Auto")) is None: continue
                self._status_message_ids[chat_id] = message_id

            await asyncio.sleep(self.STATUS_UPDATE_DELAY)


    async def _status(self, event: NewMessage.Event) -> None:
        if (chat_id := event.chat_id) is None: return
        asyncio.create_task(self._safe_delete_event(event))

        self._remove_status_message_async(chat_id)

        if (message_id := await self._safe_respond(event, sm.get_status() + "User")) is None: return
        self._status_message_ids[chat_id] = message_id


    async def _logs(self, event: NewMessage.Event) -> None:
        asyncio.create_task(self._safe_delete_event(event))

        try:
            with open(log_config.LOG_PATH, "r") as log_file:
                logs: str = log_file.read()
                if len(logs) > self.TELEGRAM_MESSAGE_LIMIT: logs = logs[-self.TELEGRAM_MESSAGE_LIMIT:]
            await self._safe_respond_cleanup(event, f"{log_config.LOG_PATH}:\n```{logs}```")
        except Exception as e:
            logger.error(f"Logs reading error: {e}")
            await self._safe_respond_cleanup(event, f"Logs reading error: {e}")


    async def _clean(self, event: NewMessage.Event) -> None:
        if (chat_id := event.chat_id) is None: return
        asyncio.create_task(self._safe_delete(chat_id, event.id))

        self._remove_status_message_async(chat_id)

        if (message_ids := self._message_ids.pop(chat_id, None)) is None: return
        await self._safe_delete(chat_id, list(message_ids))


    async def _update(self, event: NewMessage.Event) -> None:
        asyncio.create_task(self._safe_delete_event(event))

        try:
            sm.git_pull()
            await self._safe_respond_cleanup(event, "Updated")
        except Exception as e:
            logger.error(f"Update error: {e}")
            await self._safe_respond_cleanup(event, f"Update error: {e}")


    async def _restart(self, event: NewMessage.Event) -> None:
        self._is_running = False
        await asyncio.gather(
            self._safe_delete_event(event),
            self._delete_messages(),
            self._delete_status_messages()
        )

        logger.info("Restart")
        asyncio.get_event_loop().stop()


    async def _stop_bot(self, event: NewMessage.Event) -> None:
        self._is_running = False
        await asyncio.gather(
            self._safe_delete_event(event),
            self._delete_messages(),
            self._delete_status_messages()
        )

        self._client.disconnect()
        logger.info("Bot has been stopped")


    async def _help(self, event: NewMessage.Event) -> None:
        asyncio.create_task(self._safe_delete_event(event))
        await self._safe_respond_cleanup(event, """```
Commands:
    status          Show status
    logs            Show logs
    clean           Clean chat
    update          Update bot
    restart         Restart bot
    /stop-bot       Stop the bot but
                        keeping the process alive
                        Warning: This action is irreversible
    help            Show help
    version         Show version
```"""
        )


    async def _version(self, event: NewMessage.Event) -> None:
        asyncio.create_task(self._safe_delete_event(event))
        await self._safe_respond_cleanup(event, "Server Monitor Bot v2.1.0 neclor")


    async def _delete_status_messages(self) -> None:
        status_message_ids: dict[int, int] = self._status_message_ids
        self._status_message_ids = {}

        tasks: list = [self._safe_delete(chat_id, message_id) for chat_id, message_id in status_message_ids.items()]
        if tasks: await asyncio.gather(*tasks)


    async def _delete_messages(self) -> None:
        message_ids: dict[int, set[int]] = self._message_ids
        self._message_ids = {}

        tasks: list = [self._safe_delete(chat_id, list(msg_ids)) for chat_id, msg_ids in message_ids.items()]
        if tasks: await asyncio.gather(*tasks)


    def _remove_status_message_async(self, chat_id: int) -> None:
        if (message_id := self._status_message_ids.pop(chat_id, None)) is None: return
        asyncio.create_task(self._safe_delete(chat_id, message_id))


    async def _safe_respond_cleanup(self, event: NewMessage.Event, text: str) -> None:
        if (chat_id := event.chat_id) is None: return
        if (message_id := await self._safe_respond(event, text)) is None: return

        self._message_ids.setdefault(chat_id, set()).add(message_id)
        await asyncio.sleep(self.MESSAGE_LIFETIME)

        if ((message_ids := self._message_ids.get(chat_id)) is not None) and (message_id in message_ids):
            message_ids.discard(message_id)
            await self._safe_delete(chat_id, message_id)


    async def _safe_respond(self, event: NewMessage.Event, text: str) -> int | None:
        try:
            return (await event.respond(text)).id
        except Exception as e:
            logger.warning(f"Response error: {e}")
        return None


    async def _safe_send(self, chat_id: int, text: str) -> int | None:
        try:
            return (await self._client.send_message(chat_id, text)).id
        except Exception as e:
            logger.warning(f"Sending message error: {e}")
        return None


    async def _safe_delete(self, chat_id: int, message_ids: int | list[int]) -> None:
        try:
            await self._client.delete_messages(chat_id, message_ids)
        except Exception as e:
            logger.warning(f"Deleting message error: {e}")


    async def _safe_delete_event(self, event: NewMessage.Event) -> None:
        try:
            await event.delete()
        except Exception as e:
            logger.warning(f"Deleting event error: {e}")
