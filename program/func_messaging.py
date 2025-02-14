from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from decouple import config
from func_private import get_balance
from constants import HOST, ACCESS_TOKEN, PLACE_TRADES_EVENT, MANAGE_EXITS_EVENT, FIND_COINTEGRATED_EVENT, ABORT_ALL_POSITIONS_EVENT
from threading import Event
import requests
import v20

BOT_ACTIVE_EVENT = Event()

# Send message
def send_message(message):
    bot_token = config("TELEGRAM_TOKEN")
    chat_id = config("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    res = requests.get(url)
    return "sent" if res.status_code == 200 else "failed"

# Check user permission
AUTHORIZED_USER_ID = 5863260030

def is_authorized_user(func):
  async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
    user_id = update.message.from_user.id
    if user_id != AUTHORIZED_USER_ID:
      await update.message.reply_text("You are not authorized to use this bot.")
      return  # Stop execution of the command
    return await func(update, context, *args, **kwargs)
  return wrapper

# Commands
@is_authorized_user
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("Hello! This is your Forex Bot :)")

@is_authorized_user
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
    """
    This is the command system to trade in the OANDA System

    type /help for type and format of commands
    type /trade to begin trading
    type /stop to stop trade after final cycle
    type /abort to abort the program
    type /balance to check balance of account
    type /config to configure various functions
    """
  )

@is_authorized_user
async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  BOT_ACTIVE_EVENT.set()  # Signal trading to start
  await update.message.reply_text("Beginning trade!")

@is_authorized_user
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  BOT_ACTIVE_EVENT.clear()  # Signal to stop trading logic
  await update.message.reply_text("Stopping trade!")

@is_authorized_user
async def abort_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  ABORT_ALL_POSITIONS_EVENT.set()
  await update.message.reply_text("Abort program! Selling stock and stopping trade.")

@is_authorized_user
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  client = v20.Context(hostname=HOST, token=ACCESS_TOKEN, port=443)
  balance, unrealizedPL, margin = get_balance(client)
  await update.message.reply_text(
    f"""
    - Account NAV: {float(balance) + float(unrealizedPL)}
- Account balance: {balance}
- current unrealized Profit/Loss: {unrealizedPL}
- current margin used: {margin}
- current win percentage: {round(float(unrealizedPL)/(float(margin)+0.00001), 3)}
    """
    )

@is_authorized_user
async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
  f"""
  Type the following messages to configure the chatbot
  ----  
  enable/disable trade ~ Enable or disable the bot from finding new trading opportunities
  
  update cointegrated ~ Update the bot's cointegrated reference spreadsheet to more recent data

  enable/disable sell ~ Enable or disable the bot from managing current positions

  current configeration:
  Place trade = {PLACE_TRADES_EVENT.is_set()}
  Update cointegrated pairs = {FIND_COINTEGRATED_EVENT.is_set()}
  Abort all positions = {ABORT_ALL_POSITIONS_EVENT.is_set()}
  Manage positions = {MANAGE_EXITS_EVENT.is_set()}
  """
)

# Responses
def handle_response(text: str):
  processed = text.lower()
  global PLACE_TRADES
  if 'enable trade' in processed:
    PLACE_TRADES_EVENT.set()
    return "Finding new positions..."
  elif 'disable trade' in processed:
    PLACE_TRADES_EVENT.clear()
    return "Stop finding new positions..."
  if 'update cointegrated' in processed:
    FIND_COINTEGRATED_EVENT.set()
    return "Finding new cointegrated pair after this cycle..."
  if 'enable sell' in processed:
    MANAGE_EXITS_EVENT.set()
    return "Finding selling opportunities..."
  if 'disable sell' in processed:
    MANAGE_EXITS_EVENT.clear()
    return "Stop finding selling opportunities"

@is_authorized_user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message_type = update.message.chat.type
  text = update.message.text

  print(f"User ({update.message.chat.id}) in {message_type}: '{text}'")
  response = handle_response(text)
  print("Bot:", response)
  await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
  print(f'Update {update} caused error {context.error}')

# Main bot
def start_telegram_bot():
  print("Starting bot...")
  app = Application.builder().token(config("TELEGRAM_TOKEN")).build()

  # Commands
  app.add_handler(CommandHandler('start', start_command))
  app.add_handler(CommandHandler('help', help_command))
  app.add_handler(CommandHandler('trade', trade_command))
  app.add_handler(CommandHandler('stop', stop_command))
  app.add_handler(CommandHandler('abort', abort_command))
  app.add_handler(CommandHandler('balance', balance_command))
  app.add_handler(CommandHandler('config', config_command))

  # Message
  app.add_handler(MessageHandler(filters.TEXT, handle_message))

  # Error
  app.add_error_handler(error)

  # Poll the bot
  print('Polling...')
  app.run_polling(poll_interval=3)
