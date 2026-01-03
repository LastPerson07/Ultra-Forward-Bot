import logging
from flask import Flask
from threading import Thread
from config import Config

# Disable Flask's default access logs to keep your console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask("")

@app.route("/")
def home():
    return "Bot is running"

def run():
    try:
        # Use the port from Config (which defaults to 8080 but adapts to Render)
        app.run(host="0.0.0.0", port=Config.PORT)
    except Exception as e:
        logging.error(f"Keep Alive Server Error: {e}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Ensures the thread dies when the main program stops
    t.start()
