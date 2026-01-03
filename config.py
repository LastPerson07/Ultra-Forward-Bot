import os
import logging
from dotenv import load_dotenv

# Load environment variables if .env exists (useful for local testing)
load_dotenv()

class Config:
    # --- Required Credentials ---
    API_ID = int(os.environ.get("API_ID", ))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # --- Database & Sessions ---
    DB_URL = os.environ.get("DB_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "forward_bot_db")
    BOT_SESSION = os.environ.get("BOT_SESSION", "forward-bot")
    
    # --- Identity & Security ---
    # Supports space-separated or comma-separated IDs
    OWNER_ID = [int(id) for id in os.environ.get("OWNER_ID", "8496419402").replace(',', ' ').split() if id.strip().isdigit()]
    
    # --- Channel & Storage Logic ---
    # Bin Channel ID should start with -100
    BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", -1003656791142)) 
    
    # --- Big Channel & Performance Fixes ---
    # Higher worker count prevents lag in busy channels
    TG_WORKERS = int(os.environ.get("TG_WORKERS", "4")) 
    # Port for Render Web Service (assigned automatically by Render)
    PORT = int(os.environ.get("PORT", "8080")) 

class Temp:
    """
    Runtime storage that clears on restart.
    Crucial for preventing memory leaks and tracking active tasks.
    """
    lock = {}           # Track active locks per chat
    CANCEL = {}         # Track user-triggered cancellations
    forwardings = 0     # Global counter for active forward tasks
    BANNED_USERS = []   # Cache for banned IDs to save DB calls
    IS_FRWD_CHAT = []   # List of chats currently in process
