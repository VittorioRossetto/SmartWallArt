from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import json
import os
from datetime import datetime

TOKEN = "YOUR_BOT_TOKEN"
FEEDBACK_FILE = "ratings.json"
LAST_VISUAL_FILE = "last_visual.json"

# Ensure files exist
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump([], f)

def load_last_visual():
    if os.path.exists(LAST_VISUAL_FILE):
        with open(LAST_VISUAL_FILE) as f:
            return json.load(f)
    return None

def save_rating(user_id, rating):
    visual = load_last_visual()
    entry = {
        "user_id": user_id,
        "rating": rating,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "visual": visual
    }
    with open(FEEDBACK_FILE) as f:
        data = json.load(f)
    data.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

def start(update, context):
    update.message.reply_text("Welcome to SmartArt! Rate the current visual using /rate <0–5>")

def rate(update, context):
    try:
        rating = int(context.args[0])
        if 0 <= rating <= 5:
            save_rating(update.effective_user.id, rating)
            update.message.reply_text(f"Thanks! Your rating of {rating}/5 has been recorded.")
        else:
            update.message.reply_text("Rating must be between 0 and 5.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /rate <number from 0 to 5>")

def unknown(update, context):
    update.message.reply_text("Unknown command. Try /rate <0–5>")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("rate", rate))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    print("Telegram bot running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
