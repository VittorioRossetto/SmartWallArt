# Import required libraries
import os  # For environment variables
import requests  # For HTTP requests to the rating API
from dotenv import load_dotenv  # For loading environment variables from .env file
import logging  # For logging bot activity
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update  # Telegram UI elements
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters  # Telegram bot framework
)


# Load environment variables from .env file
load_dotenv()
# Get Telegram bot token from environment
TOKEN = os.getenv("BOT_TOKEN")


# === API CONFIG ===
# Get the rating API endpoint from environment (default to localhost)
VISUAL_API = os.getenv("VISUAL_API_URL", "http://localhost:5050")


# Set up logging for info and error messages
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Data Helpers ===

# === Data Helpers ===
def fetch_latest_visual():
    # Fetch the latest visual (sensor entry with motion == 1) from the rating API
    try:
        resp = requests.get(f"{VISUAL_API}/latest_visual", timeout=3)  # GET request to API
        if resp.status_code == 200:
            return resp.json()  # Return sensor data dict
        else:
            logger.warning(f"No visual found: {resp.text}")  # Log warning if not found
            return None
    except Exception as e:
        logger.error(f"Error fetching latest visual: {e}")  # Log error if request fails
        return None


def save_rating(user_id, rating, visual_time):
    # Send a rating for a visual to the rating API
    payload = {
        "user_id": user_id,  # Telegram user ID
        "rating": rating,    # Rating value (0-5)
        "visual_time": visual_time  # Timestamp of the visual being rated
    }
    try:
        resp = requests.post(f"{VISUAL_API}/rate_visual", json=payload, timeout=3)  # POST request to API
        if resp.status_code == 200:
            logger.info(f"Saved rating {rating} from user {user_id} for visual_time: {visual_time}")  # Log success
        else:
            logger.error(f"Failed to save rating: {resp.text}")  # Log failure
    except Exception as e:
        logger.error(f"Error saving rating: {e}")  # Log error if request fails

# === Handlers ===


# === Handlers ===
def start(update, context):
    # Handler for /start command. Greets the user.
    update.message.reply_text("Welcome to SmartArt! Tap /rate to rate the current visual.")  # Send welcome message


def rate_menu(update, context):
    # Handler for /rate command. Shows the rating menu for the current visual.
    visual = fetch_latest_visual()  # Get latest visual from API
    if not visual:
        update.message.reply_text("No visual available for rating right now.")  # Inform user if no visual
        return
    # Store visual_time in user_data for later use (for linking rating)
    context.user_data['visual_time'] = visual.get('time')  # Save timestamp
    # Create inline keyboard for rating (0-5 stars)
    keyboard = [
        [InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_{i}") for i in range(6)]  # 0-5 stars
    ]
    update.message.reply_text("Please rate the current visual:", reply_markup=InlineKeyboardMarkup(keyboard))  # Show rating menu


def button_handler(update: Update, context):
    # Handler for rating button presses. Saves the rating and links it to the visual.
    query = update.callback_query  # Get callback query
    query.answer()  # Acknowledge button press

    if query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])  # Extract rating value from callback data
        visual_time = context.user_data.get('visual_time')  # Get stored visual timestamp
        if not visual_time:
            query.edit_message_text(text="❌ Could not link rating to visual.")  # Error if missing
            return
        save_rating(query.from_user.id, rating, visual_time)  # Save rating to API
        query.edit_message_text(text=f"✅ Thanks for rating: {rating} ⭐")  # Confirm to user


def unknown(update, context):
    # Handler for unknown commands.
    update.message.reply_text("Unknown command. Try /rate")  # Suggest /rate command

# === Main ===

def main():
    # Main function to start the Telegram bot and register handlers.
    if not TOKEN:
        print("BOT_TOKEN not found in environment!")  # Error if token missing
        return

    updater = Updater(TOKEN, use_context=True)  # Create bot updater
    dp = updater.dispatcher  # Dispatcher for handlers

    # Register command and callback handlers
    dp.add_handler(CommandHandler("start", start))  # /start command
    dp.add_handler(CommandHandler("rate", rate_menu))  # /rate command
    dp.add_handler(CallbackQueryHandler(button_handler))  # Rating button handler
    dp.add_handler(MessageHandler(Filters.command, unknown))  # Unknown command handler

    logger.info("Bot started. Waiting for messages...")  # Log bot start
    updater.start_polling()  # Start polling for messages
    updater.idle()  # Wait for bot to finish

if __name__ == "__main__":
    main()  # Run main if script is executed
