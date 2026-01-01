from keep_alive import keep_alive
from bot import Bot

# Start web server for Render
keep_alive()

# Start Telegram bot
app = Bot()
app.run()
