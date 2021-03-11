import os
import html
import logging

import constants 
import responses

from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

logger.info('Bot started...')

def start_command(update, context):
    # Send a message when the command /start is issued.
    user = update.message.from_user
    
    context.bot.send_message(text=constants.START_MESSAGE,
                     chat_id=user.id,
                     parse_mode=ParseMode.HTML)

def help_command(update, context):
    # Send a message when the command /help is issued.
    user = update.message.from_user
    
    context.bot.send_message(text=constants.HELP_MESSAGE,
                     chat_id=user.id,
                     parse_mode=ParseMode.HTML)

def handle_message(update, context):
    text = str(update.message.text).lower()
    response = responses.send_to_group(text)
    
    # Send whatever is sent to the bot to time to entrepret group
    context.bot.send_message(text=response,
                     chat_id=constants.TIME_TO_ENTREPRET)

    # update.message.reply_text(response)

def error(update, context):
    # Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(constants.API_KEY)
    
    # Used to register handlers
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    dispatcher.add_error_handler(error)
    
    updater.start_webhook(listen="0.0.0.0",
                          port=constants.PORT,
                          url_path=constants.API_KEY)
    updater.bot.setWebhook(constants.APP_NAME + constants.API_KEY)

    # updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()