import asyncio
import logging

from telethon import TelegramClient
from telethon.events import NewMessage

from bot import message_utils as mu
from modules import server_manager as sm

from configs import api_keys, bot_config, log_config


logger: logging.Logger = logging.getLogger(__name__)


class Bot:
    def __init__(self) -> None:
        self.COMMANDS: dict[str, object] = {
            r"(?i)^(/status)$": self._status,
            r"(?i)^(/clean)$": self._clean,
            r"(?i)^(/help)$": self._help,
            r"(?i)^(/version)$": self._version,
        }
        self.ADMIN_COMMANDS: dict[str, object] = {
            r"(?i)^(/logs)$": self._logs,
            r"(?i)^(/update)$": self._update,
            r"(?i)^(/restart)$": self._restart,
            r"(?i)^(/stopbot)$": self._stop_bot,
        }

        self._client: TelegramClient = TelegramClient(api_keys.BOT_SESSION_NAME, api_keys.API_ID, api_keys.API_HASH).start(bot_token=api_keys.BOT_TOKEN)
        self._status_message_ids: dict[int | str, int] = {}
        self._message_ids: dict[int | str, set[int]] = {}

        self._is_running: bool = False

        for pattern, function in self.COMMANDS.items():
            self._client.on(NewMessage(api_keys.CHAT_IDS, pattern=pattern))(function)
        for pattern, function in self.ADMIN_COMMANDS.items():
            self._client.on(NewMessage(api_keys.CHAT_IDS, from_users=api_keys.ADMIN_IDS, pattern=pattern))(function)


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
            await asyncio.sleep(bot_config.CONNECTION_RETRY_DEALY)


    async def _autoupdate_status(self) -> None:
        await asyncio.sleep(bot_config.STATUS_UPDATE_START_DELAY)
        while self._is_running:
            if not self._client.is_connected():
                await asyncio.sleep(1)
                continue
            for chat_id in api_keys.AUTO_UPDATE_IDS:
                self._remove_status_message_async(chat_id)
                if (message_id := await mu.safe_send(self._client, chat_id, sm.get_status() + "Auto")) is None: continue
                self._status_message_ids[chat_id] = message_id
            await asyncio.sleep(bot_config.STATUS_UPDATE_DELAY)


#region Commands
    async def _status(self, event: NewMessage.Event) -> None:
        if (chat_id := event.chat_id) is None: return
        self._auto_delete_command_async(event)
        self._remove_status_message_async(chat_id)
        if (message_id := await mu.safe_respond(event, sm.get_status() + "User")) is None: return
        self._status_message_ids[chat_id] = message_id


    async def _clean(self, event: NewMessage.Event) -> None:
        if (chat_id := event.chat_id) is None: return
        self._auto_delete_command_async(event)

        self._remove_status_message_async(chat_id)

        if (message_ids := self._message_ids.pop(chat_id, None)) is None: return
        await mu.safe_delete(self._client, chat_id, list(message_ids))


    async def _help(self, event: NewMessage.Event) -> None:
        self._auto_delete_command_async(event)
        await self._safe_respond_auto_delete(event, """
**Commands**
/status - show status
/clean - clean messages
/help - show help
/version - show version

**Admin commands**
/logs - show logs
/update - update bot
/restart - restart bot
/stopbot - stop the bot but
    keeping the process alive
    Warning: This action is irreversible
"""
        )


    async def _version(self, event: NewMessage.Event) -> None:
        self._auto_delete_command_async(event)
        await self._safe_respond_auto_delete(event, "Server Monitor Bot v3.0.0 neclor")
#endregion


#region Admin commands
    async def _logs(self, event: NewMessage.Event) -> None:
        self._auto_delete_command_async(event)
        try:
            with open(log_config.LOG_PATH, "r") as log_file:
                logs: str = log_file.read()
                if len(logs) > bot_config.MESSAGE_SIZE_LIMIT: logs = logs[-bot_config.MESSAGE_SIZE_LIMIT:]
            await self._safe_respond_auto_delete(event, f"{log_config.LOG_PATH}:\n```\n{logs}```")
        except Exception as e:
            logger.error(f"Logs reading error: {e}")
            await self._safe_respond_auto_delete(event, f"Logs reading error: {e}")


    async def _update(self, event: NewMessage.Event) -> None:
        self._auto_delete_command_async(event)
        try:
            sm.git_pull()
            await self._safe_respond_auto_delete(event, "Updated")
        except Exception as e:
            logger.error(f"Update error: {e}")
            await self._safe_respond_auto_delete(event, f"Update error: {e}")


    async def _restart(self, event: NewMessage.Event) -> None:
        await self._stop_auto_delete(event)
        logger.info("Restart")
        asyncio.get_event_loop().stop()


    async def _stop_bot(self, event: NewMessage.Event) -> None:
        await self._stop_auto_delete(event)
        self._client.disconnect()
        logger.info("Bot has been stopped")
#endregion


    async def _stop_auto_delete(self, event: NewMessage.Event) -> None:
        self._is_running = False
        tasks: list = [self._delete_status_messages()]
        if bot_config.AUTO_DELETE_COMMANDS: tasks.append(mu.safe_delete_event(event))
        if bot_config.AUTO_DELETE_MESSAGES: tasks.append(self._delete_messages())
        await asyncio.gather(*tasks)


    async def _delete_status_messages(self) -> None:
        status_message_ids: dict[int | str, int] = self._status_message_ids
        self._status_message_ids = {}

        tasks: list = [mu.safe_delete(self._client, chat_id, message_id) for chat_id, message_id in status_message_ids.items()]
        if tasks: await asyncio.gather(*tasks)


    async def _delete_messages(self) -> None:
        message_ids: dict[int | str, set[int]] = self._message_ids
        self._message_ids = {}

        tasks: list = [mu.safe_delete(self._client, chat_id, list(msg_ids)) for chat_id, msg_ids in message_ids.items()]
        if tasks: await asyncio.gather(*tasks)


    def _remove_status_message_async(self, chat_id: int | str) -> None:
        if bot_config.AUTO_DELETE_STATUS: return
        if (message_id := self._status_message_ids.pop(chat_id, None)) is None: return
        asyncio.create_task(mu.safe_delete(self._client, chat_id, message_id))


    def _auto_delete_command_async(self, event: NewMessage.Event) -> None:
        if bot_config.AUTO_DELETE_COMMANDS:
            asyncio.create_task(mu.safe_delete_event(event))


    async def _safe_respond_auto_delete(self, event: NewMessage.Event, text: str) -> None:
        if (chat_id := event.chat_id) is None: return
        if (message_id := await mu.safe_respond(event, text)) is None: return

        if not bot_config.AUTO_DELETE_MESSAGES: return

        self._message_ids.setdefault(chat_id, set()).add(message_id)
        await asyncio.sleep(bot_config.MESSAGE_LIFETIME)

        if ((message_ids := self._message_ids.get(chat_id)) is not None) and (message_id in message_ids):
            message_ids.discard(message_id)
            await mu.safe_delete(self._client, chat_id, message_id)
