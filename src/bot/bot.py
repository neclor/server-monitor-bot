import asyncio

from telethon import types, TelegramClient
from telethon.events import NewMessage

from src.utils import server_monitor
from src.configs import bot_config


client: TelegramClient = TelegramClient(bot_config.TG_BOT_SESSION_PATH, bot_config.TG_BOT_API_ID, bot_config.TG_BOT_API_HASH)
_last_status_id: int | None = None


async def run() -> None:
    await client.start(bot_token=bot_config.TG_BOT_TOKEN)  # type: ignore[misc]
    asyncio.create_task(_autoupdate_status())
    await client.run_until_disconnected()  # type: ignore[misc]


async def _autoupdate_status() -> None:
    global _last_status_id

    await asyncio.sleep(bot_config.STATUS_UPDATE_START_DELAY)
    while True:
        if _last_status_id is not None:
            asyncio.create_task(client.delete_messages(bot_config.TG_BOT_CHAT_ID, _last_status_id))

        msg: types.Message = await client.send_message(bot_config.TG_BOT_CHAT_ID, await server_monitor.get_status())
        _last_status_id = msg.id
        await asyncio.sleep(bot_config.STATUS_UPDATE_DELAY)


@client.on(NewMessage(bot_config.TG_BOT_CHAT_ID, pattern=r"(?i)^(/status)$"))
async def _status(event: NewMessage.Event) -> None:
    await event.respond(await server_monitor.get_status())


@client.on(NewMessage(bot_config.TG_BOT_CHAT_ID, pattern=r"(?i)^(/help)$"))
async def _help(event: NewMessage.Event) -> None:
    await event.respond("""
**Commands**
/status - show status
/help - show help
""")
