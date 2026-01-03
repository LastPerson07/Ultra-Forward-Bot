
import os
import sys
import asyncio 
from datetime import datetime, timedelta
from database import db, mongodb_version
from config import Config, temp
from platform import python_version
from translation import Translation
from pyrogram import Client, filters, enums, __version__ as pyrogram_version
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument

# 🟢 MODERNIZED BUTTONS
main_buttons = [[
        InlineKeyboardButton('📢 Updates', url='https://t.me/Madflix_Bots'),
        InlineKeyboardButton('💬 Support', url='https://t.me/MadflixBots_Support')
        ],[
        InlineKeyboardButton('🛠️ Help', callback_data='help'),
        InlineKeyboardButton('💎 Premium', callback_data='buy_premium') # Replaced About with Premium
        ],[
        InlineKeyboardButton('👤 My Profile', callback_data='my_profile') # Added Profile
        ]]

#===================Start Function===================#

@Client.on_message(filters.private & filters.command(['start']))
async def start(client, message):
    user = message.from_user
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
    
    reply_markup = InlineKeyboardMarkup(main_buttons)
    # Professional intro animation
    jishubotz = await message.reply_sticker("CAACAgUAAxkBAAECEEBlLA-nYcsWmsNWgE8-xqIkriCWAgACJwEAAsiUZBTiPWKAkUSmmh4E")
    await asyncio.sleep(1)
    await jishubotz.delete()
    
    text = Translation.START_TXT.format(user.mention)
    await message.reply_text(
        text=text,
        reply_markup=reply_markup,
        quote=True
    )

#==================Admin: Add Premium==================#

@Client.on_message(filters.private & filters.command(['add_premium']) & filters.user(Config.OWNER_ID))
async def add_premium(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ **Usage:** `/add_premium {user_id} {days}`")
    
    try:
        user_id = int(message.command[1])
        days = int(message.command[2])
        expiry_date = datetime.now() + timedelta(days=days)
        
        await db.make_premium(user_id, expiry_date)
        
        # Log to private channel
        log_text = f"💎 **NEW PREMIUM ACTIVE**\n\n👤 **User:** `{user_id}`\n⏳ **Duration:** `{days} Days`"
        await client.send_message(Config.LOG_CHANNEL, log_text)
        
        await message.reply_text(f"✅ **VIP Status Granted** to `{user_id}` for `{days}` days.")
        
        # Notify the lucky user
        try:
            await client.send_message(user_id, "🎊 **Account Upgraded!**\n\nYou are now a Premium Member. Unlimited syncs and Forum support unlocked! 🚀")
        except: pass
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

#==================Restart Function==================#

@Client.on_message(filters.private & filters.command(['restart', "r"]) & filters.user(Config.OWNER_ID))
async def restart(client, message):
    msg = await message.reply_text(text="<i>Trying To Restarting.....</i>", quote=True)
    await asyncio.sleep(2)
    await msg.edit("<i>Server Restarted Successfully ✅</i>")
    os.execl(sys.executable, sys.executable, *sys.argv)

#==================Callback Functions==================#

@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    await query.message.edit_text(
        text=Translation.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(
            [[
            InlineKeyboardButton('🛠️ How To Use Me 🛠️', callback_data='how_to_use')
            ],[
            InlineKeyboardButton('⚙️ Settings ⚙️', callback_data='settings#main'),
            InlineKeyboardButton('📊 Stats 📊', callback_data='status')
            ],[
            InlineKeyboardButton('🔙 Back', callback_data='back')
            ]]
        ))

# 🟢 NEW: PREMIUM PROFILE UI
@Client.on_callback_query(filters.regex(r'^my_profile'))
async def profile_cb(bot, query):
    user_id = query.from_user.id
    data = await db.get_user_status(user_id)
    
    status = "💎 ᴘʀᴇᴍɪᴜᴍ" if data['is_premium'] else "🆓 ꜰʀᴇᴇ ᴛɪᴇʀ"
    quota = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if data['is_premium'] else f"{data['usage_count']} / {data['limit']}"
    expiry = data['expiry'].strftime('%Y-%m-%d') if data['expiry'] else "N/A"

    text = f"""
╭──── 👤 **ᴜsᴇʀ ᴘʀᴏꜰɪʟᴇ** ────╮
│
│  🆔 **ɪᴅ:** `{user_id}`
│  🌟 **ᴘʟᴀɴ:** `{status}`
│  📊 **ᴜsᴀɢᴇ:** `{quota}`
│  ⏳ **ᴇxᴘɪʀᴇs:** `{expiry}`
│
╰─────────────────────────────╯
**✨ ᴀʀᴄʜɪᴛᴇᴄᴛᴇᴅ ʙʏ ᴅʜᴀɴᴘᴀʟ sʜᴀʀᴍᴀ**
"""
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='back')]]))

# 🟢 NEW: BUY PREMIUM (SALES FUNNEL)
@Client.on_callback_query(filters.regex(r'^buy_premium'))
async def buy_premium_ui(bot, query):
    text = """
╭──── 💎 **ᴜʟᴛʀᴀ-ꜰᴏʀᴡᴀʀᴅ ᴘʀᴇᴍɪᴜᴍ** ────╮
│
│  **🏆 ᴇxᴄʟᴜsɪᴠᴇ ʙᴇɴᴇꜰɪᴛs:**
│  • ♾️ **ᴜɴʟɪᴍɪᴛᴇᴅ ǫᴜᴏᴛᴀ**
│  • 📂 **ᴛᴏᴘɪᴄ sᴜᴘᴘᴏʀᴛ**
│  • 🛡️ **ʙʏᴘᴀss ʀᴇsᴛʀɪᴄᴛᴇᴅ ᴄʜᴀᴛs**
│  • ⚡ **ᴍᴀx ᴅᴇʟɪᴠᴇʀʏ sᴘᴇᴇᴅ**
│
├──── 💳 **ᴘᴜʀᴄʜᴀsᴇ ɪɴꜰᴏ** ────┤
│
│  ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴅɪsᴄᴜss ᴘʀɪᴄɪɴɢ ᴀɴᴅ 
│  ᴀᴄᴛɪᴠᴀᴛᴇ ʏᴏᴜʀ sᴜʙsᴄʀɪᴘᴛɪᴏɴ.
│
╰──────────────────────────────╯
"""
    buttons = [
        [InlineKeyboardButton("💬 ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ", url="https://t.me/LastPerson07")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    reply_markup = InlineKeyboardMarkup(main_buttons)
    await query.message.edit_text(
       reply_markup=reply_markup,
       text=Translation.START_TXT.format(query.from_user.first_name))

@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    users_count, bots_count = await db.total_users_bots_count()
    total_channels = await db.total_channels()
    await query.message.edit_text(
        text=Translation.STATUS_TXT.format(users_count, bots_count, temp.forwardings, total_channels, temp.BANNED_USERS ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='help')]]),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )
