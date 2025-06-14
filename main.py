from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import logging
import datetime

# --- Configuration ---
BOT_USERNAME = "YourBotUsername"  # Replace with your bot's username
CHANNEL_INVITE_LINK = "https://t.me/+1LZkinQJTz0yZWQ1"  # Replace with your channel invite link
REFERRAL_BASE_LINK = f"https://t.me/{BOT_USERNAME}?start="

# --- Rewards ---
REFERRAL_BONUS = 5
DAILY_BONUS = 2
WITHDRAW_THRESHOLD = 50

# --- In-Memory Storage ---
user_data = {}

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Helper Functions ---
def get_referral_link(user_id):
    return f"{REFERRAL_BASE_LINK}{user_id}"


def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'balance': 0,
            'referrals': [],
            'last_bonus': None,
            'joined': False
        }


def is_bonus_claimed_today(user_id):
    return user_data[user_id]['last_bonus'] == datetime.date.today()


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("💰 Balance", callback_data='balance'),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data='daily_bonus')
        ],
         [
             InlineKeyboardButton("🎯 My Referral Link",
                                  callback_data='referral'),
             InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')
         ],
         [InlineKeyboardButton("❓ How to Earn", callback_data='how_to_earn')]])


def back_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]])


# --- Command Handlers ---
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    args = context.args

    init_user(user_id)

    # Referral logic
    if args:
        ref_id = int(args[0])
        if ref_id != user_id:
            init_user(ref_id)
            if user_id not in user_data[ref_id]['referrals']:
                user_data[ref_id]['referrals'].append(user_id)
                user_data[ref_id]['balance'] += REFERRAL_BONUS

    # Channel join enforcement
    if not user_data[user_id]['joined']:
        join_text = (
            "📢 *Important Step!*\n\n"
            "To activate your earnings dashboard, please join our official channel first:\n"
            f"{CHANNEL_INVITE_LINK}\n\n"
            "After joining, tap the ✅ button below.")
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ I Joined",
                                   callback_data="verify_join")]])
        update.message.reply_text(join_text,
                                  reply_markup=keyboard,
                                  parse_mode="Markdown")
        return

    # User passed join check
    welcome_msg = (f"👋 Hello {user.first_name}!\n\n"
                   "🎉 Welcome to the *Refer & Earn* bot.\n"
                   "Earn rewards by inviting friends and completing tasks.\n")
    update.message.reply_text(welcome_msg,
                              parse_mode="Markdown",
                              reply_markup=main_menu_keyboard())


# --- Callback Query Handler ---
def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    init_user(user_id)
    query.answer()

    if query.data == 'verify_join':
        # Channel join verification simulation
        user_data[user_id]['joined'] = True
        query.edit_message_text("✅ You have successfully joined the channel!",
                                reply_markup=main_menu_keyboard())
        return

    if not user_data[user_id]['joined']:
        query.edit_message_text(
            "❌ You must join the channel first to access the bot.")
        return

    # Handle main menu options
    if query.data == 'menu':
        query.edit_message_text("🏠 *Main Menu*",
                                parse_mode="Markdown",
                                reply_markup=main_menu_keyboard())

    elif query.data == 'balance':
        bal = user_data[user_id]['balance']
        query.edit_message_text(f"💰 Your current balance: ₹{bal}",
                                reply_markup=back_button())

    elif query.data == 'referral':
        link = get_referral_link(user_id)
        refs = len(user_data[user_id]['referrals'])
        msg = (f"🎯 *Your Referral Link:*\n`{link}`\n\n"
               f"👥 Total referrals: *{refs}*")
        query.edit_message_text(msg,
                                parse_mode="Markdown",
                                reply_markup=back_button())

    elif query.data == 'withdraw':
        bal = user_data[user_id]['balance']
        if bal >= WITHDRAW_THRESHOLD:
            user_data[user_id]['balance'] = 0
            query.edit_message_text(f"📤 Withdrawal of ₹{bal} requested!",
                                    reply_markup=back_button())
        else:
            query.edit_message_text(
                f"❌ Minimum balance of ₹{WITHDRAW_THRESHOLD} required for withdrawal.\n"
                f"Your current balance: ₹{bal}",
                reply_markup=back_button())

    elif query.data == 'how_to_earn':
        msg = ("💡 *How to Earn Money*\n\n"
               "- Share your referral link with friends 👥\n"
               f"- Earn ₹{REFERRAL_BONUS} for each friend who joins.\n"
               f"- Claim a daily bonus of ₹{DAILY_BONUS} 🎁\n"
               f"- Withdraw when your balance reaches ₹{WITHDRAW_THRESHOLD} 📤")
        query.edit_message_text(msg,
                                parse_mode="Markdown",
                                reply_markup=back_button())

    elif query.data == 'daily_bonus':
        if is_bonus_claimed_today(user_id):
            query.edit_message_text(
                "🎁 You already claimed today’s bonus. Come back tomorrow!",
                reply_markup=back_button())
        else:
            user_data[user_id]['balance'] += DAILY_BONUS
            user_data[user_id]['last_bonus'] = datetime.date.today()
            query.edit_message_text(
                f"🎉 You received a daily bonus of ₹{DAILY_BONUS}!",
                reply_markup=back_button())


# --- Error Handling ---
def error_handler(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error: {context.error}")


# --- Main Bot Execution ---
def main():
    TOKEN = "7561306874:AAGqrcxpHao8qVhxg1kfK0q_1j9Qyw9P_Rc"  # Replace with your bot token
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(handle_buttons))
    dp.add_error_handler(error_handler)

    print("✅ Bot is running...")
    updater.start_polling()
    updater.idle()

from keep_alive import keep_alive
keep_alive()
