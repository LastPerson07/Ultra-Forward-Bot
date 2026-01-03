import time as tm
from database import db 
from .test import parse_buttons

# Global runtime dictionary to track task statuses
STATUS = {}

class STS:
    def __init__(self, id):
        self.id = id
        self.data = STATUS
    
    def verify(self):
        """Verifies if the task ID exists in the runtime memory."""
        return self.data.get(self.id)
    
    def store(self, From, to, skip, limit):
        """Initializes and stores a new forwarding task session."""
        self.data[self.id] = {
            "FROM": From, 
            'TO': to, 
            'total_files': 0, 
            'skip': int(skip) if skip else 0, 
            'limit': int(limit) if limit else 0,
            'fetched': int(skip) if skip else 0, 
            'filtered': 0, 
            'deleted': 0, 
            'duplicate': 0, 
            'total': int(limit) if limit else 0, 
            'start': 0
        }
        # Populate object attributes for direct access (e.g., sts.FROM)
        return self.get(full=True)
        
    def get(self, value=None, full=False):
        """Retrieves task data or populates the object instance."""
        values = self.data.get(self.id)
        if not values:
            return None
        if not full:
            return values.get(value)
        
        # This allows calling sts.FROM instead of sts.get('FROM')
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def add(self, key=None, value=1, time=False):
        """Increments task counters or sets the start time."""
        if self.id not in self.data:
            return
        if time:
            return self.data[self.id].update({'start': tm.time()})
        
        current_val = self.data[self.id].get(key, 0)
        self.data[self.id].update({key: current_val + value}) 
    
    def divide(self, no, by):
        """Safe division for progress bar calculation."""
        by = 1 if int(by) == 0 else by 
        return float(no) / by 
    
    async def get_data(self, user_id):
        """Fetches complete user configuration for the forwarding engine."""
        bot = await db.get_bot(user_id)
        # Ensure object attributes are ready for the return statement
        self.get(full=True)
        
        filters = await db.get_filters(user_id)
        configs = await db.get_configs(user_id)
        size = None
        
        # Handle duplicate detection settings
        if configs.get('duplicate', True):
            duplicate = [configs.get('db_uri'), getattr(self, 'TO', None)]
        else:
            duplicate = False
            
        button = parse_buttons(configs.get('button', ''))
        
        if configs.get('file_size', 0) != 0:
            size = [configs['file_size'], configs.get('size_limit')]
            
        return (
            bot, 
            configs.get('caption'), 
            configs.get('forward_tag'), 
            {
                'chat_id': getattr(self, 'FROM', None), 
                'limit': getattr(self, 'limit', 0), 
                'offset': getattr(self, 'skip', 0), 
                'filters': filters,
                'keywords': configs.get('keywords'), 
                'media_size': size, 
                'extensions': configs.get('extensions'), 
                'skip_duplicate': duplicate
            }, 
            configs.get('protect'), 
            button
        )

def get_readable_time(seconds: int) -> str:
    """Converts raw seconds into a human-readable format."""
    result = ""
    (days, remainder) = divmod(int(seconds), 86400)
    if days > 0:
        result += f"{int(days)}d "
    (hours, remainder) = divmod(remainder, 3600)
    if hours > 0:
        result += f"{int(hours)}h "
    (minutes, seconds) = divmod(remainder, 60)
    if minutes > 0:
        result += f"{int(minutes)}m "
    result += f"{int(seconds)}s"
    return result.strip()
