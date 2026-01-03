# Fixed config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.environ.get("API_ID", 0)) # Fixed trailing comma
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    DB_URL = os.environ.get("DB_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "forward_bot_db")
    BOT_SESSION = os.environ.get("BOT_SESSION", "forward-bot")
    OWNER_ID = [int(id) for id in os.environ.get("OWNER_ID", "8496419402").replace(',', ' ').split() if id.strip().isdigit()]
    BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", -1003656791142)) 
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -1003656791142)) # Added missing variable
    TG_WORKERS = int(os.environ.get("TG_WORKERS", "4")) 
    PORT = int(os.environ.get("PORT", "8080")) 

class Temp:
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
