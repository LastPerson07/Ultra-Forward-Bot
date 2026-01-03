import asyncio
import logging 
import logging.config
from database import db 
from config import Config  
from pyrogram import Client, __version__
from pyrogram.raw.all import layer 
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait 

# Safe logging initialization to prevent crash if file is missing
try:
    logging.config.fileConfig('logging.conf')
except Exception:
    logging.basicConfig(level=logging.INFO)

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client): 
    def __init__(self):
        super().__init__(
            name=Config.BOT_SESSION, # Replaced positional arg with 'name' for clarity
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            plugins={
                "root": "plugins"
            },
            workers=50,
            bot_token=Config.BOT_TOKEN
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"{me.first_name} with for pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        
        # Using Default ParseMode as per your original code
        self.set_parse_mode(ParseMode.DEFAULT)
        
        text = "**Bot Restarted !**"
        logging.info("Sending restart notification...")
        
        success = failed = 0
        
        # Logic for Big Channels: Iterate through notify list
        users = await db.get_all_frwd()
        async for user in users:
            chat_id = user['user_id']
            try:
                await self.send_message(chat_id, text)
                success += 1
            except FloodWait as e:
                # Essential for Big Channels to avoid getting banned by Telegram
                await asyncio.sleep(e.value + 1)
                await self.send_message(chat_id, text)
                success += 1
            except Exception:
                failed += 1 

        # Summary of the broadcast
        if (success + failed) != 0:
            await db.rmve_frwd(all=True)
            logging.info(f"Restart message status - Success: {success}, Failed: {failed}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        logging.info(msg)
