MY_SESSION_NAME: str = "me"
BOT_SESSION_NAME: str = "bot"

API_ID: int = 0
API_HASH: str = "API Hash"
BOT_TOKEN: str = "Bot Token"

ADMIN_IDS: set[int | str] = set()
AUTO_UPDATE_IDS: set[int | str] = set()
CHAT_IDS: set[int | str] = {*ADMIN_IDS, *AUTO_UPDATE_IDS,
}
