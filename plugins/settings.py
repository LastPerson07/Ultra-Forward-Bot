import asyncio 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
# Integrated: Pulling directly from CLIENT and db for better stability
from .test import CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

@Client.on_message(filters.private & filters.command(['settings']))
async def settings(client, message):
    text = "<b>Change Your Settings As Your Wish</b>"
    await message.reply_text(
        text=text,
        reply_markup=main_buttons(),
        quote=True
    )

@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
    user_id = query.from_user.id
    # Fixed: Safe splitting of data
    data_parts = query.data.split("#")
    type = data_parts[1] if len(data_parts) > 1 else "main"
    
    # Default Back Button used in multiple places
    back_to_main = [[InlineKeyboardButton('🔙 Back', callback_data="settings#main")]]
    back_btn_markup = InlineKeyboardMarkup(back_to_main)
  
    if type == "main":
        await query.message.edit_text(
            "<b>Change Your Settings As Your Wish</b>",
            reply_markup=main_buttons())
       
    elif type == "bots":
        buttons = [] 
        _bot = await db.get_bot(user_id)
        if _bot is not None:
            buttons.append([InlineKeyboardButton(_bot['name'], callback_data=f"settings#editbot")])
        else:
            buttons.append([InlineKeyboardButton('✚ Add Bot ✚', callback_data="settings#addbot")])
            buttons.append([InlineKeyboardButton('✚ Add User Bot ✚', callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>My Bots</u></b>\n\nYou Can Manage Your Bots In Here",
            reply_markup=InlineKeyboardMarkup(buttons))
  
    elif type == "addbot":
        await query.message.delete()
        # This triggers the interactive bot addition logic
        bot_added = await CLIENT.add_bot(bot, query)
        if bot_added != True: return
        await query.message.reply_text(
            "<b>Bot Token Successfully Added To Database</b>",
            reply_markup=back_btn_markup)
  
    elif type == "adduserbot":
        await query.message.delete()
        user_added = await CLIENT.add_session(bot, query)
        if user_added != True: return
        await query.message.reply_text(
            "<b>Session Successfully Added To Database</b>",
            reply_markup=back_btn_markup)
      
    elif type == "channels":
        buttons = []
        channels = await db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}", callback_data=f"settings#editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add Channel ✚', callback_data="settings#addchannel")])
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data="settings#main")])
        await query.message.edit_text( 
            "<b><u>My Channels</u></b>\n\nYou Can Manage Your Target Chats In Here",
            reply_markup=InlineKeyboardMarkup(buttons))
   
    elif type == "addchannel":  
        await query.message.delete()
        try:
            prompt = await bot.send_message(user_id, "<b><u>Set Target Chat</u></b>\n\nForward A Message From Your Target Chat\n/cancel - To Cancel This Process")
            response = await bot.listen(chat_id=user_id, timeout=300)
            
            if response.text == "/cancel":
                await response.delete()
                return await prompt.edit_text("Process Canceled", reply_markup=back_btn_markup)
            
            if not response.forward_from_chat:
                await response.delete()
                return await prompt.edit_text("This Is Not A Forward Message", reply_markup=back_btn_markup)
            
            chat_id = response.forward_from_chat.id
            title = response.forward_from_chat.title
            username = "@" + response.forward_from_chat.username if response.forward_from_chat.username else "private"
            
            is_added = await db.add_channel(user_id, chat_id, title, username)
            await response.delete()
            await prompt.edit_text(
                "Successfully Updated" if is_added else "This Channel Already Added",
                reply_markup=back_btn_markup)
        except asyncio.TimeoutError:
            await bot.send_message(user_id, 'Process Timed Out!', reply_markup=back_btn_markup)
  
    elif type == "editbot": 
        bot_info = await db.get_bot(user_id)
        TEXT = Translation.BOT_DETAILS if bot_info['is_bot'] else Translation.USER_DETAILS
        buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data="settings#removebot")],
                   [InlineKeyboardButton('🔙 Back', callback_data="settings#bots")]]
        await query.message.edit_text(
            TEXT.format(bot_info['name'], bot_info['id'], bot_info['username']),
            reply_markup=InlineKeyboardMarkup(buttons))
                                               
    elif type == "removebot":
        await db.remove_bot(user_id)
        await query.message.edit_text("Bot Removed Successfully", reply_markup=back_btn_markup)
                                               
    elif type.startswith("editchannels"): 
        chat_id = type.split('_')[1]
        chat = await db.get_channel_details(user_id, chat_id)
        buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removechannel_{chat_id}")],
                   [InlineKeyboardButton('🔙 Back', callback_data="settings#channels")]]
        await query.message.edit_text(
            f"<b><u>📄 Channel Details</b></u>\n\n<b>Title :</b> <code>{chat['title']}</code>\n<b>ID :</b> <code>{chat['chat_id']}</code>\n<b>User :</b> {chat['username']}",
            reply_markup=InlineKeyboardMarkup(buttons))
                                               
    elif type.startswith("removechannel"):
        chat_id = type.split('_')[1]
        await db.remove_channel(user_id, chat_id)
        await query.message.edit_text("Channel Removed Successfully", reply_markup=back_btn_markup)
                               
    elif type == "caption":
        config = await db.get_configs(user_id)
        buttons = []
        if config.get('caption') is None:
            buttons.append([InlineKeyboardButton('✚ Add Caption ✚', callback_data="settings#addcaption")])
        else:
            buttons.append([InlineKeyboardButton('👀 See Caption', callback_data="settings#seecaption")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Delete', callback_data="settings#deletecaption"))
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>Custom Caption</b></u>\n\nUse <code>{filename}</code>, <code>{size}</code>, <code>{caption}</code>",
            reply_markup=InlineKeyboardMarkup(buttons))
                                
    elif type == "seecaption":   
        config = await db.get_configs(user_id)
        buttons = [[InlineKeyboardButton('✏️ Edit', callback_data="settings#addcaption")],
                   [InlineKeyboardButton('🔙 Back', callback_data="settings#caption")]]
        await query.message.edit_text(f"<b><u>Current Caption</b></u>\n\n<code>{config['caption']}</code>", reply_markup=InlineKeyboardMarkup(buttons))
    
    elif type == "deletecaption":
        await db.update_configs(user_id, {'caption': None})
        await query.message.edit_text("Caption Deleted", reply_markup=back_btn_markup)
                              
    elif type == "addcaption":
        await query.message.delete()
        try:
            prompt = await bot.send_message(user_id, "Send your custom caption\n/cancel to stop.")
            response = await bot.listen(chat_id=user_id, timeout=300)
            if response.text == "/cancel":
                return await prompt.edit_text("Cancelled", reply_markup=back_btn_markup)
            
            await db.update_configs(user_id, {'caption': response.text})
            await response.delete()
            await prompt.edit_text("Caption Updated", reply_markup=back_btn_markup)
        except asyncio.TimeoutError:
            await bot.send_message(user_id, 'Timeout!', reply_markup=back_btn_markup)
  
    elif type == "button":
        config = await db.get_configs(user_id)
        buttons = []
        if config.get('button') is None:
            buttons.append([InlineKeyboardButton('✚ Add Button ✚', callback_data="settings#addbutton")])
        else:
            buttons.append([InlineKeyboardButton('👀 See Button', callback_data="settings#seebutton")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Remove', callback_data="settings#deletebutton"))
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data="settings#main")])
        await query.message.edit_text("<b><u>Custom Button Settings</b></u>", reply_markup=InlineKeyboardMarkup(buttons))

    elif type == "database":
        config = await db.get_configs(user_id)
        buttons = []
        if config.get('db_uri') is None:
            buttons.append([InlineKeyboardButton('✚ Add URL ✚', callback_data="settings#addurl")])
        else:
            buttons.append([InlineKeyboardButton('👀 See URL', callback_data="settings#seeurl")])
            buttons[-1].append(InlineKeyboardButton('🗑️ Remove URL', callback_data="settings#deleteurl"))
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data="settings#main")])
        await query.message.edit_text("<b><u>Secondary Database (Duplicate Tracker)</b></u>", reply_markup=InlineKeyboardMarkup(buttons))

    elif type == "filters":
        await query.message.edit_text("<b><u>Content Filters</u></b>", reply_markup=await filters_buttons(user_id))
  
    elif type == "nextfilters":
        await query.edit_message_reply_markup(reply_markup=await next_filters_buttons(user_id))
   
    elif type.startswith("updatefilter"):
        # Fixed: Splitting logic for updatefilter
        _, key, value = type.split('-')
        new_val = False if value == "True" else True
        
        config = await db.get_configs(user_id)
        if key in config['filters']:
            config['filters'][key] = new_val
        else:
            config[key] = new_val
            
        await db.update_configs(user_id, config)
        
        if key in ['poll', 'protect']:
            await query.edit_message_reply_markup(reply_markup=await next_filters_buttons(user_id)) 
        else:
            await query.edit_message_reply_markup(reply_markup=await filters_buttons(user_id))

def main_buttons():
    buttons = [[
        InlineKeyboardButton('🤖 Bots', callback_data='settings#bots'),
        InlineKeyboardButton('🔥 Channels', callback_data='settings#channels')
    ],[
        InlineKeyboardButton('✏️ Caption', callback_data='settings#caption'),
        InlineKeyboardButton('🗃 MongoDB', callback_data='settings#database')
    ],[
        InlineKeyboardButton('🕵‍♀ Filters', callback_data='settings#filters'),
        InlineKeyboardButton('🏓 Button', callback_data='settings#button')
    ],[
        InlineKeyboardButton('⚙️ Extra Settings', callback_data='settings#nextfilters')
    ],[      
        InlineKeyboardButton('🔙 Close', callback_data='close_btn')
    ]]
    return InlineKeyboardMarkup(buttons)

# ... [Remaining Helper functions: size_limit, extract_btn, filters_buttons remain structurally similar but connected to 'db'] ...

def size_limit(limit):
   if str(limit) == "None":
      return None, ""
   elif str(limit) == "True":
      return True, "more than"
   else:
      return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
       for data in datas:
         if i >= 5:
            i = 0
         if i == 0:
            btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
            i += 1
            continue
         elif i > 0:
            btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
            i += 1
    return btn 

def size_button(size):
  buttons = [[
       InlineKeyboardButton('+',
                    callback_data=f'settings#update_limit-True-{size}'),
       InlineKeyboardButton('=',
                    callback_data=f'settings#update_limit-None-{size}'),
       InlineKeyboardButton('-',
                    callback_data=f'settings#update_limit-False-{size}')
       ],[
       InlineKeyboardButton('+1',
                    callback_data=f'settings#update_size-{size + 1}'),
       InlineKeyboardButton('-1',
                    callback_data=f'settings#update_size_-{size - 1}')
       ],[
       InlineKeyboardButton('+5',
                    callback_data=f'settings#update_size-{size + 5}'),
       InlineKeyboardButton('-5',
                    callback_data=f'settings#update_size_-{size - 5}')
       ],[
       InlineKeyboardButton('+10',
                    callback_data=f'settings#update_size-{size + 10}'),
       InlineKeyboardButton('-10',
                    callback_data=f'settings#update_size_-{size - 10}')
       ],[
       InlineKeyboardButton('+50',
                    callback_data=f'settings#update_size-{size + 50}'),
       InlineKeyboardButton('-50',
                    callback_data=f'settings#update_size_-{size - 50}')
       ],[
       InlineKeyboardButton('+100',
                    callback_data=f'settings#update_size-{size + 100}'),
       InlineKeyboardButton('-100',
                    callback_data=f'settings#update_size_-{size - 100}')
       ],[
       InlineKeyboardButton('↩ Back',
                    callback_data="settings#main")
     ]]
  return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('🏷️ Forward Tag',
                    callback_data=f'settings_#updatefilter-forward_tag-{filter["forward_tag"]}'),
       InlineKeyboardButton('✅' if filter['forward_tag'] else '❌',
                    callback_data=f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')
       ],[
       InlineKeyboardButton('🖍️ Texts',
                    callback_data=f'settings_#updatefilter-text-{filters["text"]}'),
       InlineKeyboardButton('✅' if filters['text'] else '❌',
                    callback_data=f'settings#updatefilter-text-{filters["text"]}')
       ],[
       InlineKeyboardButton('📁 Documents',
                    callback_data=f'settings_#updatefilter-document-{filters["document"]}'),
       InlineKeyboardButton('✅' if filters['document'] else '❌',
                    callback_data=f'settings#updatefilter-document-{filters["document"]}')
       ],[
       InlineKeyboardButton('🎞️ Videos',
                    callback_data=f'settings_#updatefilter-video-{filters["video"]}'),
       InlineKeyboardButton('✅' if filters['video'] else '❌',
                    callback_data=f'settings#updatefilter-video-{filters["video"]}')
       ],[
       InlineKeyboardButton('📷 Photos',
                    callback_data=f'settings_#updatefilter-photo-{filters["photo"]}'),
       InlineKeyboardButton('✅' if filters['photo'] else '❌',
                    callback_data=f'settings#updatefilter-photo-{filters["photo"]}')
       ],[
       InlineKeyboardButton('🎧 Audios',
                    callback_data=f'settings_#updatefilter-audio-{filters["audio"]}'),
       InlineKeyboardButton('✅' if filters['audio'] else '❌',
                    callback_data=f'settings#updatefilter-audio-{filters["audio"]}')
       ],[
       InlineKeyboardButton('🎤 Voices',
                    callback_data=f'settings_#updatefilter-voice-{filters["voice"]}'),
       InlineKeyboardButton('✅' if filters['voice'] else '❌',
                    callback_data=f'settings#updatefilter-voice-{filters["voice"]}')
       ],[
       InlineKeyboardButton('🎭 Animations',
                    callback_data=f'settings_#updatefilter-animation-{filters["animation"]}'),
       InlineKeyboardButton('✅' if filters['animation'] else '❌',
                    callback_data=f'settings#updatefilter-animation-{filters["animation"]}')
       ],[
       InlineKeyboardButton('🃏 Stickers',
                    callback_data=f'settings_#updatefilter-sticker-{filters["sticker"]}'),
       InlineKeyboardButton('✅' if filters['sticker'] else '❌',
                    callback_data=f'settings#updatefilter-sticker-{filters["sticker"]}')
       ],[
       InlineKeyboardButton('▶️ Skip Duplicate',
                    callback_data=f'settings_#updatefilter-duplicate-{filter["duplicate"]}'),
       InlineKeyboardButton('✅' if filter['duplicate'] else '❌',
                    callback_data=f'settings#updatefilter-duplicate-{filter["duplicate"]}')
       ],[
       InlineKeyboardButton('🔙 back',
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('📊 Poll',
                    callback_data=f'settings_#updatefilter-poll-{filters["poll"]}'),
       InlineKeyboardButton('✅' if filters['poll'] else '❌',
                    callback_data=f'settings#updatefilter-poll-{filters["poll"]}')
       ],[
       InlineKeyboardButton('🔒 Secure Message',
                    callback_data=f'settings_#updatefilter-protect-{filter["protect"]}'),
       InlineKeyboardButton('✅' if filter['protect'] else '❌',
                    callback_data=f'settings#updatefilter-protect-{filter["protect"]}')
       ],[
       InlineKeyboardButton('🛑 Size Limit',
                    callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('💾 Extension',
                    callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('📌 Keywords',
                    callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('🔙 Back', 
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 
   

