import os
from dotenv import load_dotenv


load_dotenv()


STATUS_UPDATE_START_DELAY: int = int(os.getenv("STATUS_UPDATE_START_DELAY", "60"))
STATUS_UPDATE_DELAY: int = int(os.getenv("STATUS_UPDATE_DELAY", "600"))

TG_BOT_API_ID: int = int(os.getenv("TG_BOT_API_ID", "0"))
TG_BOT_API_HASH: str = os.getenv("TG_BOT_API_HASH", "")
TG_BOT_TOKEN: str = os.getenv("TG_BOT_TOKEN", "")
TG_BOT_SESSION_PATH: str = os.getenv("TG_BOT_SESSION_PATH", "/data/bot")
TG_BOT_CHAT_ID: int = int(os.getenv("TG_BOT_CHAT_ID", "0"))
