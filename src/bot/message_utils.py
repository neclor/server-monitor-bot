import logging

from telethon import TelegramClient
from telethon.events import NewMessage


logger: logging.Logger = logging.getLogger(__name__)


async def safe_send(client: TelegramClient, chat_id: int | str, text: str) -> int | None:
    try:
        return (await client.send_message(chat_id, text)).id
    except Exception as e:
        logger.warning(f"Sending message error: {e}")
    return None


async def safe_delete(client: TelegramClient, chat_id: int | str, message_ids: int | list[int]) -> None:
    try:
        await client.delete_messages(chat_id, message_ids)
    except Exception as e:
        logger.warning(f"Deleting message error: {e}")


async def safe_respond(event: NewMessage.Event, text: str) -> int | None:
    try:
        return (await event.respond(text)).id
    except Exception as e:
        logger.warning(f"Response error: {e}")
    return None


async def safe_delete_event(event: NewMessage.Event) -> None:
    try:
        await event.delete()
    except Exception as e:
        logger.warning(f"Deleting event error: {e}")
