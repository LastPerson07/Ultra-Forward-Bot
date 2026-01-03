import os
import re 
import sys
import typing
import asyncio 
import logging 
from database import db 
from config import Config, Temp as temp # Fixed case-sensitivity
from pyrogram import Client, filters
from pyrogram.raw.all import layer
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from pyrogram.errors import FloodWait
from translation import Translation

from typing import Union, Optional, AsyncGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")
BOT_TOKEN_TEXT = "1) Create A Bot Using @BotFather\n\n2) Then You Will Get A Message With Bot Token\n\n3) Forward That Message To Me"
SESSION_STRING_SIZE = 351

async def start_clone_bot(FwdBot):
    """Starts the client and injects the iter_messages method safely."""
    await FwdBot.start()
    
    async def iter_messages(
        self, 
        chat_id: Union[int, str], 
        limit: int, 
        offset: int = 0,
    ) -> Optional[AsyncGenerator["Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            # Fetching messages by ID range
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1

    # Bind the method to the specific instance
    FwdBot.iter_messages = iter_messages.__get__(FwdBot, Client)
    FwdBot.me = await FwdBot.get_me()
    return FwdBot

class CLIENT: 
    def __init__(self):
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
    
    def client(self, data, is_userbot=None):
        """Generates a Client instance for Bot or Userbot."""
        if is_userbot:
            return Client(
                name="USERBOT_SESSION", 
                api_id=self.api_id, 
                api_hash=self.api_hash, 
                session_string=data,
                in_memory=True
            )
        else:
            return Client(
                name="CLONE_BOT", 
                api_id=self.api_id, 
                api_hash=self.api_hash, 
                bot_token=data, 
                in_memory=True
            )

    async def add_bot(self, bot, query):
        user_id = int(query.from_user.id)
        msg = await bot.ask(chat_id=user_id, text=BOT_TOKEN_TEXT)
        
        if msg.text == '/cancel':
            return await msg.reply('Process Cancelled !')
        if not msg.forward_date:
            return await msg.reply_text("This Is Not A Forward Message")
        if str(msg.forward_from.id) != "93372553":
            return await msg.reply_text("This Message Was Not Forwarded From @BotFather")
            
        bot_token_re = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text, re.IGNORECASE)
        bot_token = bot_token_re[0] if bot_token_re else None
        
        if not bot_token:
            return await msg.reply_text("There Is No Bot Token In That Message")
            
        try:
            _client = await start_clone_bot(self.client(bot_token, is_userbot=False))
            _bot = _client.me
            details = {
                'id': _bot.id,
                'is_bot': True,
                'user_id': user_id,
                'name': _bot.first_name,
                'token': bot_token,
                'username': _bot.username 
            }
            await db.add_bot(details)
            await _client.stop()
            return True
        except Exception as e:
            await msg.reply_text(f"<b>Bot Error:</b> `{e}`")
            return False

    async def add_session(self, bot, query):
        user_id = int(query.from_user.id)
        text = "<b>⚠️ Disclaimer ⚠️</b>\n\nYou can use your session to forward messages from private chats. Added at your own risk."
        await bot.send_message(user_id, text=text)
        
        msg = await bot.ask(chat_id=user_id, text="<b>Send your Pyrogram Session String.</b>\n/cancel to stop.")
        
        if msg.text == '/cancel':
            return await msg.reply('Process Cancelled !')
        if len(msg.text) < SESSION_STRING_SIZE:
            return await msg.reply('Invalid Session String')
            
        try:
            _client = await start_clone_bot(self.client(msg.text, is_userbot=True))
            user = _client.me
            details = {
                'id': user.id,
                'is_bot': False,
                'user_id': user_id,
                'name': user.first_name,
                'session': msg.text,
                'username': user.username
            }
            await db.add_bot(details)
            await _client.stop()
            return True
        except Exception as e:
            await msg.reply_text(f"<b>User Bot Error:</b> `{e}`")
            return False

@Client.on_message(filters.private & filters.command('reset'))
async def reset_settings(bot, m):
    # Using a fixed template ID or default dict
    default = await db.get_configs("DEFAULT") # Standardize this ID
    if not default:
        return await m.reply("Default settings not found.")
    await db.update_configs(m.from_user.id, default)
    await m.reply("Successfully Settings Reseted ✔️")

@Client.on_message(filters.command('resetall') & filters.user(Config.OWNER_ID))
async def resetall_cmd(bot, message):
    users = await db.get_all_users()
    sts = await message.reply("Processing...")
    progress_text = "Total: {}\nSuccess: {}\nFailed: {}"
    total = success = failed = 0
    
    async for user in users:
        user_id = user['id']
        total += 1
        try:
            current = await db.get_configs(user_id)
            current['db_uri'] = None
            await db.update_configs(user_id, current)
            success += 1
        except:
            failed += 1
        
        if total % 10 == 0:
            await sts.edit(progress_text.format(total, success, failed))
            
    await sts.edit("Completed\n" + progress_text.format(total, success, failed))

async def get_configs(user_id):
    """Helper to fetch configs from DB."""
    return await db.get_configs(user_id)

async def update_configs(user_id, key, value):
    """Helper to update specific config keys or filters."""
    current = await db.get_configs(user_id)
    if key in ['caption', 'duplicate', 'db_uri', 'forward_tag', 'protect', 'file_size', 'size_limit', 'extension', 'keywords', 'button']:
        current[key] = value
    else: 
        current['filters'][key] = value
    await db.update_configs(user_id, current)

def parse_buttons(text, markup=True):
    """Parses custom button format into Pyrogram InlineKeyboardMarkup."""
    buttons = []
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            btn_text = match.group(2)
            btn_url = match.group(3).replace(" ", "")
            if bool(match.group(4)) and buttons:
                buttons[-1].append(InlineKeyboardButton(text=btn_text, url=btn_url))
            else:
                buttons.append([InlineKeyboardButton(text=btn_text, url=btn_url)])
                
    if markup and buttons:
        return InlineKeyboardMarkup(buttons)
    return buttons if buttons else None
