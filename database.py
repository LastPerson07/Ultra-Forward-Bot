from config import Config
import motor.motor_asyncio
from pymongo import MongoClient
from datetime import datetime

async def mongodb_version():
    """Checks MongoDB version without breaking the async loop."""
    # Using a sync client briefly is fine for a one-time startup check
    x = MongoClient(Config.DB_URL)
    version = x.server_info()['version']
    x.close() # Always close manual connections
    return version

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.col = self.db.users
        self.nfy = self.db.notify
        self.chl = self.db.channels 
        
    def new_user(self, id, name):
        """Standardizes the user document structure."""
        return dict(
            id=int(id),
            name=name,
            is_premium=False,
            expiry=None,
            usage_count=0,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
            configs=None # Initialize as None to avoid KeyErrors later
        )
      
    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            user = self.new_user(id, name)
            await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    async def make_premium(self, user_id, expiry_date):
        await self.col.update_one(
            {'id': int(user_id)}, 
            {'$set': {'is_premium': True, 'expiry': expiry_date}}
        )

    async def remove_premium(self, user_id):
        await self.col.update_one(
            {'id': int(user_id)}, 
            {'$set': {'is_premium': False, 'expiry': None}}
        )

    async def increment_usage(self, user_id, count=1):
        await self.col.update_one(
            {'id': int(user_id)}, 
            {'$inc': {'usage_count': count}}
        )

    async def get_user_status(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        if user:
            return {
                'is_premium': user.get('is_premium', False),
                'expiry': user.get('expiry'),
                'usage_count': user.get('usage_count', 0),
                'limit': 50
            }
        return {'is_premium': False, 'expiry': None, 'usage_count': 0, 'limit': 50}
    
    async def total_users_bots_count(self):
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    async def total_channels(self):
        return await self.chl.count_documents({})
    
    async def remove_ban(self, id):
        ban_status = dict(is_banned=False, ban_reason='')
        await self.col.update_one({'id': int(id)}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(is_banned=True, ban_reason=ban_reason)
        await self.col.update_one({'id': int(user_id)}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(is_banned=False, ban_reason='')
        user = await self.col.find_one({'id': int(id)})
        return user.get('ban_status', default) if user else default

    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
 
    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        return [user['id'] async for user in users]

    async def update_configs(self, id, configs):
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})
         
    async def get_configs(self, id):
        default = {
            'caption': None, 'duplicate': True, 'forward_tag': False,
            'file_size': 0, 'size_limit': None, 'extension': None,
            'keywords': None, 'protect': None, 'button': None,
            'db_uri': None, 'thread_id': 0, 
            'filters': {
                'poll': True, 'text': True, 'audio': True, 'voice': True,
                'video': True, 'photo': True, 'document': True,
                'animation': True, 'sticker': True
            }
        }
        user = await self.col.find_one({'id': int(id)})
        if user and user.get('configs'):
            res = user['configs']
            # Ensure new keys don't break old user records
            if 'thread_id' not in res: res['thread_id'] = 0
            return res
        return default 
       
    async def add_bot(self, datas):
       if not await self.is_bot_exist(datas['user_id']):
          await self.bot.insert_one(datas)
    
    async def remove_bot(self, user_id):
       await self.bot.delete_many({'user_id': int(user_id)})
      
    async def get_bot(self, user_id: int):
       return await self.bot.find_one({'user_id': int(user_id)})
                                          
    async def is_bot_exist(self, user_id):
       bot = await self.bot.find_one({'user_id': int(user_id)})
       return bool(bot)
                                          
    async def in_channel(self, user_id: int, chat_id: int) -> bool:
       channel = await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
       return bool(channel)
    
    async def add_channel(self, user_id: int, chat_id: int, title, username):
       if await self.in_channel(user_id, chat_id):
         return False
       return await self.chl.insert_one({
           "user_id": int(user_id), 
           "chat_id": int(chat_id), 
           "title": title, 
           "username": username
       })
    
    async def remove_channel(self, user_id: int, chat_id: int):
       return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})
    
    async def get_channel_details(self, user_id: int, chat_id: int):
       return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
       
    async def get_user_channels(self, user_id: int):
       channels = self.chl.find({"user_id": int(user_id)})
       return [channel async for channel in channels]
     
    async def get_filters(self, user_id):
       configs = await self.get_configs(user_id)
       filter_dict = configs.get('filters', {})
       return [str(k) for k, v in filter_dict.items() if v is False]
              
    async def add_frwd(self, user_id):
       # Prevent duplicate entries in notify collection
       if not await self.nfy.find_one({'user_id': int(user_id)}):
           return await self.nfy.insert_one({'user_id': int(user_id)})
    
    async def rmve_frwd(self, user_id=0, all=False):
       query = {} if all else {'user_id': int(user_id)}
       return await self.nfy.delete_many(query)
    
    async def get_all_frwd(self):
       return self.nfy.find({})

# Instance used by other files
db = Database(Config.DB_URL, Config.DB_NAME)
