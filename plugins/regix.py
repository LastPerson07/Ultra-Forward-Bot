import os
import sys 
import math
import time
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
# Fixed: Importing Temp as temp to match your class name in config.py
from config import Config, Temp as temp
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    
    # Corrected lock check
    if temp.lock.get(user) == True:
        return await message.answer("Please Wait Until Previous Task Complete", show_alert=True)
    
    sts = STS(frwd_id)
    if not sts.verify():
        await message.answer("Your Are Clicking On My Old Button", show_alert=True)
        return await message.message.delete()
        
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
        return await message.answer("In Target Chat A Task Is Progressing. Please Wait Until Task Complete", show_alert=True)
        
    m = await msg_edit(message.message, "Verifying Your Data's, Please Wait.")
    
    # 🟢 PATCH: Fetch Premium & Quota Status
    user_status = await db.get_user_status(user)
    is_vip = user_status['is_premium']
    
    # 🟢 PATCH: Quota Guard (Lead Generation for Admin)
    if not is_vip and user_status['usage_count'] >= user_status['limit']:
        # Safety check for LOG_CHANNEL
        log_channel = getattr(Config, 'LOG_CHANNEL', None)
        if log_channel:
            await bot.send_message(log_channel, f"⚠️ **QUOTA ALERT**\n👤 User: `{user}`\nStatus: `Free Tier` (Limit Hit)")
        
        btn = [[InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_premium")]]
        return await msg_edit(m, "⚠️ **Free Quota Exhausted!**\n\nUpgrade to Premium for unlimited syncs.", InlineKeyboardMarkup(btn))

    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    configs = await db.get_configs(user)
    thread_id = configs.get('thread_id', 0)
    
    if not _bot:
        return await msg_edit(m, "You Didn't Added Any Bot. Please Add A Bot Using /settings !", wait=True)
        
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
        return await m.edit(f"Error starting client: {e}")
    
    # 🟢 PATCH: Seamless Topic Discovery for Forums
    try:
        source_chat = await client.get_chat(sts.get("FROM"))
        if getattr(source_chat, 'is_forum', False) and thread_id == 0:
            await stop(client, user)
            return await show_topic_ui(bot, message, sts.get("FROM"), frwd_id)
    except Exception as e:
        logger.error(f"Forum Discovery Failed: {e}")

    await msg_edit(m, "Processing...")
    
    try: 
        await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
        await msg_edit(m, f"Source Chat May Be Private. Use Userbot or make [Bot](t.me/{_bot['username']}) Admin.", retry_btn(frwd_id), True)
        return await stop(client, user)
        
    try:
        k = await client.send_message(i.TO, "Testing")
        await k.delete()
    except:
        await msg_edit(m, f"Please make your [UserBot / Bot](t.me/{_bot['username']}) Admin in Target Channel.", retry_btn(frwd_id), True)
        return await stop(client, user)
        
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "🩷 Forwarding Started")
    sts.add(time=True)
    
    sleep = 0.5 if _bot.get('is_bot', True) else 1.5
    
    await msg_edit(m, "Processing...") 
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    
    if locked:
        try:
            MSG = []
            pling=0
            await edit(m, 'Progressing', 10, sts)
            
            # Corrected iter_messages/get_chat_history usage
            async for message in client.get_chat_history(
                chat_id=sts.get('FROM'), 
                limit=int(sts.get('limit')), 
                offset_id=int(sts.get('skip')) if sts.get('skip') else 0
            ):
                if await is_cancelled(client, user, m, sts):
                    return
                
                # 🟢 PATCH: Mid-sync Quota Check
                if not is_vip:
                    if (user_status['usage_count'] + sts.get('fetched')) >= user_status['limit']:
                        await send(client, user, "⚠️ **Quota Reached!** Upgrade for more.")
                        break

                if pling % 50 == 0: 
                    await edit(m, 'Progressing', 10, sts)
                pling += 1
                
                sts.add('fetched')
                if message == "DUPLICATE":
                    sts.add('duplicate')
                    continue 
                elif message == "FILTERED":
                    sts.add('filtered')
                    continue 
                if message.empty or message.service:
                    sts.add('deleted')
                    continue
                    
                if forward_tag:
                    MSG.append(message.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    if (notcompleted >= 100 or completed <= 100): 
                        await forward(client, MSG, m, sts, protect)
                        sts.add('total_files', notcompleted)
                        # 🟢 Update DB usage
                        await db.increment_usage(user, notcompleted)
                        await asyncio.sleep(5) 
                        MSG = []
                else:
                    new_caption = custom_caption(message, caption)
                    details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect}
                    await copy(client, details, m, sts)
                    sts.add('total_files')
                    # 🟢 Update DB usage
                    await db.increment_usage(user, 1)
                    await asyncio.sleep(sleep) 
                    
        except Exception as e:
            await msg_edit(m, f'<b>Error :</b>\n<code>{e}</code>', wait=True)
        finally:
            if i.TO in temp.IS_FRWD_CHAT:
                temp.IS_FRWD_CHAT.remove(i.TO)
            
            configs['thread_id'] = 0
            await db.update_configs(user, configs)
            
            # 📢 LOG: Task Completion
            log_channel = getattr(Config, 'LOG_CHANNEL', None)
            if log_channel:
                log_txt = f"✅ **TASK FINISHED**\n👤 User: `{user}`\n📥 Files: `{sts.get('fetched')}`\n💎 VIP: `{is_vip}`"
                await bot.send_message(log_channel, log_txt)
            
            await send(client, user, "🎉 Forwarding Completed")
            await edit(m, 'Completed', "completed", sts) 
            await stop(client, user)

# ... [The remaining Helper Functions and Topic UI logic as provided] ...

# 🟢 TOPIC UI HELPER
async def show_topic_ui(bot, query, chat_id, frwd_id):
    user_id = query.from_user.id
    sts = STS(frwd_id)
    _bot, _, _, _, _, _ = await sts.get_data(user_id)
    client = await start_clone_bot(CLIENT.client(_bot))
    topics = []
    async for topic in client.get_forum_topics(int(chat_id)):
        topics.append(topic)
    
    if not topics:
        query.data = f"start_public_{frwd_id}"
        await client.stop()
        return await pub_(bot, query)

    buttons = []
    for i in range(0, len(topics), 2):
        row = [InlineKeyboardButton(f"📁 {topics[i].title}", f"save_topic#{topics[i].id}#{frwd_id}")]
        if i + 1 < len(topics):
            row.append(InlineKeyboardButton(f"📁 {topics[i+1].title}", f"save_topic#{topics[i+1].id}#{frwd_id}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔄 Mirror Full Group", f"save_topic#0#{frwd_id}")])
    
    await bot.edit_message_text(query.message.chat.id, query.message.id, 
                                "**📍 ꜰᴏʀᴜᴍ sᴜᴘᴘᴏʀᴛ**\n\nᴅᴇᴛᴇᴄᴛᴇᴅ ᴍᴜʟᴛɪᴘʟᴇ ᴛᴏᴘɪᴄs. sᴇʟᴇᴄᴛ ᴏɴᴇ:",
                                reply_markup=InlineKeyboardMarkup(buttons))
    await client.stop()

# 🟢 CALLBACK: SAVE TOPIC
@Client.on_callback_query(filters.regex(r'^save_topic'))
async def save_topic_callback(bot, query):
    _, topic_id, frwd_id = query.data.split("#")
    configs = await db.get_configs(query.from_user.id)
    configs['thread_id'] = int(topic_id)
    await db.update_configs(query.from_user.id, configs)
    await query.answer("Topic Locked! 🚀", show_alert=True)
    query.data = f"start_public_{frwd_id}"
    await pub_(bot, query)

# --- HELPER FUNCTIONS ---

async def copy(bot, msg, m, sts):
    try:                                  
        if msg.get("media") and msg.get("caption"):
            await bot.send_cached_media(sts.get('TO'), msg.get("media"), caption=msg.get("caption"), reply_markup=msg.get('button'), protect_content=msg.get("protect"))
        else:
            await bot.copy_message(sts.get('TO'), sts.get('FROM'), msg.get("msg_id"), caption=msg.get("caption"), reply_markup=msg.get('button'), protect_content=msg.get("protect"))
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await copy(bot, msg, m, sts)
    except Exception: sts.add('deleted')

async def forward(bot, msg, m, sts, protect):
    try:                             
        await bot.forward_messages(sts.get('TO'), sts.get('FROM'), message_ids=msg, protect_content=protect)
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await forward(bot, msg, m, sts, protect)

PROGRESS = """
╭── 📊 Transfer Status ──╮
│ 📈 {0}% Completed
│ 📥 Fetched   : {1}
│ 🚀 Sent      : {2}
│ ⏳ Left      : {3}
│ ⚡ Status    : {4}
│ ⏱️ ETA       : {5}
╰──────────────────────╯
"""

async def msg_edit(msg, text, button=None, wait=None):
    try: return await msg.edit(text, reply_markup=button)
    except MessageNotModified: pass 
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, button, wait)

async def edit(msg, title, status, sts):
    i = sts.get(full=True)
    status = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
    total = float(i.total) if i.total else 1.0
    percentage = "{:.0f}".format(float(i.fetched)*100/total)
    now, diff = time.time(), int(time.time() - i.start)
    speed = sts.divide(i.fetched, diff)
    elapsed_time, spd = round(diff) * 1000, speed if speed > 0 else 1
    time_to_completion = round(sts.divide(i.total - i.fetched, int(spd))) * 1000
    estimated_total_time = elapsed_time + time_to_completion  
    progress = "▰{0}{1}".format(''.join(["▰" for _ in range(math.floor(int(percentage) / 10))]), ''.join(["▱" for _ in range(10 - math.floor(int(percentage) / 10))]))
    button = [[InlineKeyboardButton(title, f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
    estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
    estimated_total_time = estimated_total_time if estimated_total_time != '' else '0 s'
    text = TEXT.format(i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, status, percentage, estimated_total_time, progress)
    if status in ["cancelled", "completed"]:
        button.append([InlineKeyboardButton('📢 Updates', url='https://t.me/Madflix_Bots'), InlineKeyboardButton('💬 Support', url='https://t.me/MadflixBots_Support')])
    else: button.append([InlineKeyboardButton('✖️ Cancel ✖️', 'terminate_frwd')])
    await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
    if temp.CANCEL.get(user)==True:
        if sts.TO in temp.IS_FRWD_CHAT: temp.IS_FRWD_CHAT.remove(sts.TO)
        await edit(msg, "Cancelled", "completed", sts)
        await send(client, user, "❌ Forwarding Process Cancelled")
        await stop(client, user)
        return True 
    return False 

async def stop(client, user):
    try: await client.stop()
    except: pass 
    await db.rmve_frwd(user)
    temp.forwardings -= 1
    temp.lock[user] = False 

async def send(bot, user, text):
    try: await bot.send_message(user, text=text)
    except: pass 

def custom_caption(msg, caption):
    if msg.media and (msg.video or msg.document or msg.audio or msg.photo):
        media_obj = getattr(msg, msg.media.value, None)
        if media_obj:
            file_name, file_size, fcaption = getattr(media_obj, 'file_name', ''), getattr(media_obj, 'file_size', ''), getattr(msg, 'caption', '')
            if fcaption: fcaption = fcaption.html
            return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption) if caption else fcaption
    return None

def get_size(size):
    units, size, i = ["Bytes", "KB", "MB", "GB", "TB"], float(size), 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

def media(msg):
    if msg.media:
        obj = getattr(msg, msg.media.value, None)
        return getattr(obj, 'file_id', None)
    return None 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + ((str(hours) + "h, ") if hours else "") + ((str(minutes) + "m, ") if minutes else "") + ((str(seconds) + "s, ") if seconds else "") + ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id): return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ Retry ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    temp.lock[m.from_user.id], temp.CANCEL[m.from_user.id] = False, True 
    await m.answer("Forwarding Cancelled !", show_alert=True)

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    fetched, forwarded = (sts.get('fetched'), sts.get('total_files')) if sts.verify() else (0,0)
    remaining = max(0, fetched - forwarded)
    est_time = TimeFormatter(milliseconds=est_time) if (TimeFormatter(milliseconds=est_time) != '' or status not in ['completed', 'cancelled']) else '0 s'
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()
    if update.message.reply_to_message: await update.message.reply_to_message.delete()
