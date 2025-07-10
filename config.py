import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

BOT_PREFIX = "!"
BOT_NAME = "SquareCloud Bot"
BOT_VERSION = "1.0.0"

ADMIN_ONLY_COMMANDS = ["key", "status", "deploy", "delete"]

SERVER_KEYS_FILE = "data/server_keys.json"

COLORS = {
    "success": 0x00ff00,
    "error": 0xff0000,
    "warning": 0xff9900,
    "info": 0x0099ff,
    "neutral": 0x808080
}