import os
import html
import logging

import constants 
import responses

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters

# Set states
QUESTION = range(1)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

logger.info('Bot started...')

def start(update, context):
    """
    Send a message when the command /start is issued.
    """
    user = update.message.from_user
    
    button_list = [[InlineKeyboardButton(text='See Categories', callback_data='categories')],
                   [InlineKeyboardButton(text='Ask Questions', callback_data='questions')],
                   [InlineKeyboardButton(text='Cancel', callback_data='cancel')]]
    keyboard = InlineKeyboardMarkup(button_list)
    
    context.bot.send_message(text=constants.START_MESSAGE,
                     chat_id=user.id,
                     reply_markup=keyboard,
                     parse_mode=ParseMode.HTML)

def help(update, context):
    """
    Send a message when the command /help is issued.
    """
    user = update.message.from_user
    
    context.bot.send_message(text=constants.HELP_MESSAGE,
                     chat_id=user.id,
                     parse_mode=ParseMode.HTML)

def ask_question(update, context):
    """
    Allow user to ask questions to organisations.
    """
    text = str(update.message.text).lower()
    response = responses.send_to_group(text)
    
    # Send whatever is sent to the bot to time to entrepret group
    context.bot.send_message(text=response,
                     chat_id=constants.TIME_TO_ENTREPRET,
                     parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END

def cancel(update, context):
    """
    User cancelation function. Cancel conversation by user.
    """
    user = update.message.from_user
    logger.info("User {} canceled the conversation.".format(user.first_name))
    
    context.bot.send_message(text=constants.CANCEL_MESSAGE,
                             chat_id=user.id,
                             parse_mode=ParseMode.HTML)

    return ConversationHandler.END

def error(update, context):
    # Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(constants.API_KEY)
    
    # Used to register handlers
    dispatcher = updater.dispatcher
    
    # Add conversation handler with predefined states:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            QUESTION: [MessageHandler(Filters.text, ask_question)]
        },

        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('help', help)],
        
        allow_reentry = True
    )
    
    dispatcher.add_handler(conv_handler)

    dispatcher.add_error_handler(error)
    
    updater.start_webhook(listen="0.0.0.0",
                          port=constants.PORT,
                          url_path=constants.API_KEY)
    updater.bot.setWebhook(constants.APP_NAME + constants.API_KEY)
    
    updater.idle()

if __name__ == '__main__':
    main()