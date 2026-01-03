import re
import asyncio 
from .utils import STS
from database import db
from config import temp, Config # 🟢 Added Config for Owner/Log access
from translation import Translation
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait 
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate as PrivateChat
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified, ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

#===================Run Function===================#

@Client.on_message(filters.private & filters.command(["fwd", "forward"]))
async def run(bot, message):
    buttons = []
    btn_data = {}
    user_id = message.from_user.id
    
    # 🟢 INTEGRATION: Check Subscription & Quota Status
    user_status = await db.get_user_status(user_id)
    is_vip = user_status['is_premium']
    
    # 🟢 QUOTA GUARD: Block free users who hit the limit before they even start
    if not is_vip and user_status['usage_count'] >= user_status['limit']:
        # 📢 LOG: Important Lead Alert
        await bot.send_message(Config.LOG_CHANNEL, f"⚠️ **QUOTA ATTEMPT**\n👤 User: `{user_id}`\nStatus: `FREE` (Limit Hit)")
        
        text = f"""
╭──── 💎 **ǫᴜᴏᴛᴀ ᴇxʜᴀᴜsᴛᴇᴅ** ────╮
│
│  **ʏᴏᴜ ʜᴀᴠᴇ ᴜsᴇᴅ:** `{user_status['usage_count']}/{user_status['limit']}`
│  ꜰʀᴇᴇ ᴍᴇssᴀɢᴇs ᴀʟʟᴏᴡᴇᴅ.
│
│  ᴘʟᴇᴀsᴇ **ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ** │  ᴛᴏ ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ sʏɴᴄɪɴɢ!
│
╰─────────────────────────────╯
"""
        btn = [[InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_premium")]]
        return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn))

    _bot = await db.get_bot(user_id)
    if not _bot:
        return await message.reply("You Did Not Added Any Bot. Please Add A Bot Using /settings !")
        
    channels = await db.get_user_channels(user_id)
    if not channels:
        return await message.reply_text("Please Set A To Channel In /settings Before Forwarding")

    # Step 1: Select Target Channel
    if len(channels) > 1:
        for channel in channels:
            buttons.append([KeyboardButton(f"{channel['title']}")])
            btn_data[channel['title']] = channel['chat_id']
        buttons.append([KeyboardButton("cancel")]) 
        
        _toid = await bot.ask(message.chat.id, Translation.TO_MSG.format(_bot['name'], _bot['username']), reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True))
        
        if _toid.text.lower().startswith(('/', 'cancel')):
            return await message.reply_text(Translation.CANCEL, reply_markup=ReplyKeyboardRemove())
            
        to_title = _toid.text
        toid = btn_data.get(to_title)
        if not toid:
            return await message.reply_text("Wrong Channel Choosen !", reply_markup=ReplyKeyboardRemove())
    else:
        toid = channels[0]['chat_id']
        to_title = channels[0]['title']

    # Step 2: Get Source (Link or Forward)
    fromid = await bot.ask(message.chat.id, Translation.FROM_MSG, reply_markup=ReplyKeyboardRemove())
    if fromid.text and fromid.text.startswith('/'):
        await message.reply(Translation.CANCEL)
        return 
        
    if fromid.text and not fromid.forward_date:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(fromid.text.replace("?single", ""))
        if not match:
            return await message.reply('Invalid Link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif fromid.forward_from_chat and fromid.forward_from_chat.type in [enums.ChatType.CHANNEL]:
        last_msg_id = fromid.forward_from_message_id
        chat_id = fromid.forward_from_chat.username or fromid.forward_from_chat.id
        if last_msg_id == None:
            return await message.reply_text("This May Be A Forwarded Message From A Group. Please send the link of the last message instead.")
    else:
        await message.reply_text("Invalid Source Chat Type!")
        return 

    # Step 3: Get Title and Chat Info
    try:
        title = (await bot.get_chat(chat_id)).title
    except (PrivateChat, ChannelPrivate, ChannelInvalid):
        title = "private" if fromid.text else fromid.forward_from_chat.title
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link Specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

    # Step 4: Get Skip Limit
    skipno = await bot.ask(message.chat.id, Translation.SKIP_MSG)
    if skipno.text.startswith('/'):
        await message.reply(Translation.CANCEL)
        return

    # Final Step: Double Check & Task Creation
    forward_id = f"{user_id}-{skipno.id}"
    buttons = [[
        InlineKeyboardButton('✅ ᴄᴏɴꜰɪʀᴍ', callback_data=f"start_public_{forward_id}"),
        InlineKeyboardButton('✖️ ᴄᴀɴᴄᴇʟ', callback_data="close_btn")
    ]]
    
    # 💎 Dhanpal Sharma Premium Confirmation UI
    check_text = f"""
╭─── 📡 **ꜰᴏʀᴡᴀʀᴅ ᴄᴏɴꜰɪʀᴍᴀᴛɪᴏɴ** ───╮
│
│ 🤖 **ʙᴏᴛ    :** `{_bot['name']}`
│ 📥 **ꜰʀᴏᴍ   :** `{title}`
│ 📤 **ᴛᴏ     :** `{to_title}`
│ ⏳ **sᴋɪᴘ   :** `{skipno.text}`
│ 📊 **ᴘʟᴀɴ   :** `{'💎 Premium' if is_vip else '🆓 Free'}`
│
╰─────────────────────────────╯
**✨ ᴀʀᴄʜɪᴛᴇᴄᴛᴇᴅ ʙʏ ᴅʜᴀɴᴘᴀʟ sʜᴀʀᴍᴀ**
"""
    await message.reply_text(
        text=check_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # Store data for the callback to handle
    STS(forward_id).store(chat_id, toid, int(skipno.text), int(last_msg_id))
