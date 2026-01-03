import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- Required Credentials ---
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # --- Database & Sessions ---
    DB_URL = os.environ.get("DB_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "forward_bot_db")
    BOT_SESSION = os.environ.get("BOT_SESSION", "forward-bot")
    
    # --- Identity & Security ---
    # Split by space or comma, then convert to int. Handles empty strings safely.
    OWNER_ID = [int(id) for id in os.environ.get("OWNER_ID", "").replace(',', ' ').split() if id.strip().isdigit()]
    
    # --- "Big Channel" & Performance Fixes ---
    # Increase workers for concurrent message handling in big channels
    TG_WORKERS = int(os.environ.get("TG_WORKERS", "100")) 
    # Max messages to process in a single batch to avoid memory spikes
    MAX_BATCH_SIZE = 200 
    # Port for Render Web Service
    PORT = int(os.environ.get("PORT", "8080")) 

class Temp:
    """
    Runtime storage that clears on restart.
    Used for tracking active processes and anti-spam.
    """
    lock = {}           # To prevent multiple actions on one chat
    CANCEL = {}         # To track cancellation requests
    forwardings = 0     # Global counter for active tasks
    BANNED_USERS = []   # Cached list of banned IDs for speed
    IS_FRWD_CHAT = []   # List of chats currently being processed
