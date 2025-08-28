import os
import requests
from dotenv import load_dotenv
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# === API CONFIG ===
VISUAL_API = os.getenv("VISUAL_API_URL", "http://localhost:5050")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Data Helpers ===
def fetch_latest_visual():
    try:
        resp = requests.get(f"{VISUAL_API}/latest_visual", timeout=3)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.warning(f"No visual found: {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching latest visual: {e}")
        return None

def save_rating(user_id, rating, visual_time):
    payload = {
        "user_id": user_id,
        "rating": rating,
        "visual_time": visual_time
    }
    try:
        resp = requests.post(f"{VISUAL_API}/rate_visual", json=payload, timeout=3)
        if resp.status_code == 200:
            logger.info(f"Saved rating {rating} from user {user_id} for visual_time: {visual_time}")
        else:
            logger.error(f"Failed to save rating: {resp.text}")
    except Exception as e:
        logger.error(f"Error saving rating: {e}")

# === Handlers ===

def start(update, context):
    update.message.reply_text("Welcome to SmartArt! Tap /rate to rate the current visual.")

def rate_menu(update, context):
    visual = fetch_latest_visual()
    if not visual:
        update.message.reply_text("No visual available for rating right now.")
        return
    # Store visual_time in user_data for later use
    context.user_data['visual_time'] = visual.get('time')
    keyboard = [
        [InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_{i}") for i in range(6)]
    ]
    update.message.reply_text("Please rate the current visual:", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context):
    query = update.callback_query
    query.answer()

    if query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])
        visual_time = context.user_data.get('visual_time')
        if not visual_time:
            query.edit_message_text(text="❌ Could not link rating to visual.")
            return
        save_rating(query.from_user.id, rating, visual_time)
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
