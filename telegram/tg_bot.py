import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
)

# === Setup ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

FEEDBACK_FILE = "ratings.json"
LAST_VISUAL_FILE = "last_visual.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Data Helpers ===
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

    data = []
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE) as f:
            data = json.load(f)
    data.append(entry)

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved rating {rating} from user {user_id} with visual: {visual}")

# === Handlers ===
def start(update, context):
    update.message.reply_text("Welcome to SmartArt! Tap /rate to rate the current visual.")

def rate_menu(update, context):
    keyboard = [
        [InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_{i}") for i in range(6)]
    ]
    update.message.reply_text("Please rate the current visual:", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context):
    query = update.callback_query
    query.answer()

    if query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])
        save_rating(query.from_user.id, rating)
        query.edit_message_text(text=f"✅ Thanks for rating: {rating} ⭐")

def unknown(update, context):
    update.message.reply_text("Unknown command. Try /rate")

# === Main ===
def main():
    if not TOKEN:
        print("BOT_TOKEN not found in environment!")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("rate", rate_menu))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    logger.info("Bot started. Waiting for messages...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
