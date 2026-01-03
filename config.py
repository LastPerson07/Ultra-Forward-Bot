import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # --- Required Credentials ---
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # --- Database Config ---
    DB_URL = os.environ.get("DB_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "forward_bot_db")
    
    # --- Session & Identity ---
    BOT_SESSION = os.environ.get("BOT_SESSION", "forward-bot")
    # Converts a space-separated string of IDs into a list of integers
    OWNER_ID = [int(id) for id in os.environ.get("OWNER_ID", "").split() if id.isdigit()]
    
    # --- Optional Settings ---
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))  # For logging bot actions
    PREFIX = os.environ.get("PREFIX", ".").split()     # Command prefixes

class Temp:
    """Runtime temporary storage (reset on restart)"""
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
