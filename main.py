import logging
from keep_alive import keep_alive
from bot import Bot
from config import Config

# Start web server for Render in the background
try:
    keep_alive()
    logging.info("Keep-alive server started.")
except Exception as e:
    logging.error(f"Failed to start keep-alive server: {e}")

async def main():
    # Final safety check before starting the bot
    if not Config.API_ID or not Config.BOT_TOKEN:
        logging.critical("API_ID or BOT_TOKEN is missing! Check your environment variables.")
        return

    app = Bot()
    
    # app.run() is a blocking call that keeps the bot alive
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    import asyncio
    # Using run() is standard for Pyrogram Client
    app = Bot()
    app.run()
