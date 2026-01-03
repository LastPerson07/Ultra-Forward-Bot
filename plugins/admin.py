import os, sys, asyncio, time
from config import *
from database import *
from .utils import get_readable_time
from translation import *
from datetime import datetime, timedelta # 🟢 ADDED: For Premium calculations
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup 

botStartTime = time.time()

#================== Latency Check ==================#

@Client.on_message(filters.private & filters.command(["ping", "p"]))
async def ping(_, message):
    start_t = time.time()
    rm = await message.reply_text("📡 `ᴘɪɴɢɪɴɢ sʏsᴛᴇᴍ...`", quote=True)
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rm.edit(f"🚀 **sʏsᴛᴇᴍ ʟᴀᴛᴇɴᴄʏ**\n⏱️ `{time_taken_s:.3f} ms`")

#================== Engine Analytics ==================#

@Client.on_message(filters.command(["stats", "status", "s"]) & filters.user(Config.OWNER_ID))
async def get_stats(bot, message):
    # Fetching real-time data from DB
    users_count, bots_count = await db.total_users_bots_count()
    total_channels = await db.total_channels()
    uptime = get_readable_time(time.time() - botStartTime)    
    
    st = await message.reply('**🔍 sᴄᴀɴɴɪɴɢ ᴄᴏʀᴇ ᴍᴇᴛʀɪᴄs...**')    
    
    # 💎 HIGH-END ANALYTICS UI
    stats_text = f"""
╭──── 📊 **sʏsᴛᴇᴍ ᴀɴᴀʟʏᴛɪᴄs** ────╮
│
│ ⌚ **ᴜᴘᴛɪᴍᴇ     :** `{uptime}`
│ 🐌 **ʟᴀᴛᴇɴᴄʏ    :** `{st.date - message.date}s`
│ 👤 **ᴛᴏᴛᴀʟ ᴜsᴇʀs :** `{users_count}`
│
├──── ⚡ **ᴇɴɢɪɴᴇ sᴛᴀᴛᴜs** ────┤
│
│ 🤖 **ʙᴏᴛ ʜᴜʙ     :** `{bots_count}`
│ 📡 **ʟɪᴠᴇ sʏɴᴄs  :** `{temp.forwardings}`
│ 🔥 **ᴄʜᴀɴɴᴇʟs    :** `{total_channels}`
│ 🚫 **ʀᴇsᴛʀɪᴄᴛᴇᴅ  :** `{temp.BANNED_USERS}`
│
╰─────────────────────────────╯
**✨ ᴀʀᴄʜɪᴛᴇᴄᴛᴇᴅ ʙʏ ᴅʜᴀɴᴘᴀʟ sʜᴀʀᴍᴀ**
"""
    await st.edit(text=stats_text)

#================== VIP Management ==================#

# 🟢 ADDED: Unified Admin command to grant Premium access
@Client.on_message(filters.command("add_premium") & filters.user(Config.OWNER_ID))
async def grant_premium(bot, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ **Usage:** `/add_premium {user_id} {days}`")
    
    try:
        user_id = int(message.command[1])
        days = int(message.command[2])
        expiry_date = datetime.now() + timedelta(days=days)
        
        await db.make_premium(user_id, expiry_date)
        
        # 📢 LOG: Send to Admin Log Channel
        log_txt = f"💎 **NEW VIP ACTIVE**\n👤 User: `{user_id}`\n⏳ Days: `{days}`"
        await bot.send_message(Config.LOG_CHANNEL, log_txt)
        
        await message.reply_text(f"✅ **VIP Status Granted** to `{user_id}` for {days} days.")
        try:
            await bot.send_message(user_id, "🎊 **Your account is now Premium!** Sync limits removed.")
        except: pass
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")

#================== Sponsorship Hub ==================#

@Client.on_message(filters.private & filters.command(["donate", "d"]))
async def donate(client, message):
    # 💎 MODERNIZED SALES/DONATION UI
    text = """
╭──── 🎁 **sᴘᴏɴsᴏʀsʜɪᴘ ʜᴜʙ** ────╮
│
│  ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ sᴜᴘᴘᴏʀᴛɪɴɢ 
│  ᴍʏ ᴡᴏʀᴋ! ʏᴏᴜʀ ᴄᴏɴᴛʀɪʙᴜᴛɪᴏɴs 
│  ᴋᴇᴇᴘ ᴛʜᴇ sᴇʀᴠᴇʀs ʀᴜɴɴɪɴɢ.
│
├──── 💳 **ᴘᴀʏᴍᴇɴᴛ ɪɴꜰᴏ** ────┤
│
│ 🛍️ **ᴜᴘɪ ɪᴅ :** `madflixofficial@axl`
│ 💬 **ᴀᴅᴍɪɴ  :** @LastPerson07
│
╰─────────────────────────────╯
*ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ᴀꜰᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ.*
"""
    keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🦋 Contact Owner", url="https://t.me/LastPerson07"), 
                    InlineKeyboardButton("✖️ Close", callback_data="close_btn")]])
    await message.reply_text(text=text, reply_markup=keyboard)
