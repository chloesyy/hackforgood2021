import os
import html
import logging

import constants 
import responses

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters

# Set states
CHOICE, QUESTION, CATEGORIES = range(3)

# Callback data
CATEGORIES, QUESTIONS, CANCEL = range(3)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

logger.info('Bot started...')

def start(update, context):
    """
    Send a message when the command /start is issued.
    """
    logger.info('State: START')
    user = update.message.from_user
    
    button_list = [[InlineKeyboardButton(text='See Categories', callback_data='categories')],
                   [InlineKeyboardButton(text='Ask Questions', callback_data='questions')],
                   [InlineKeyboardButton(text='Cancel', callback_data='cancel')]]
    keyboard = InlineKeyboardMarkup(button_list)
    
    context.bot.send_message(text=constants.START_MESSAGE,
                     chat_id=user.id,
                     reply_markup=keyboard,
                     parse_mode=ParseMode.HTML)
    
    return CHOICE

def help(update, context):
    """
    Send a message when the command /help is issued.
    """
    user = update.message.from_user
    
    context.bot.send_message(text=constants.HELP_MESSAGE,
                     chat_id=user.id,
                     parse_mode=ParseMode.HTML)

def question_intro(update, context):
    """
    Question intro line
    """
    logger.info('State: CHOICE - Waiting for question...')

    query = update.callback_query
    update.answer_callback_query(query.id, text=query.data)
    
    context.bot.send_message(text=constants.QUESTION_MESSAGE,
                             chat_id=query.message.chat_id,
                             parse_mode=ParseMode.HTML)
    
    return QUESTION

def ask_question(update, context):
    """
    Allow user to ask questions to organisations.
    """
    logger.info('State: QUESTION')

    user = update.message.from_user
    
    text = str(update.message.text).lower()
    response = responses.send_to_group(text)
    
    # Send whatever is sent to the bot to time to entrepret group
    context.bot.send_message(text=response,
                     chat_id=constants.TIME_TO_ENTREPRET,
                     parse_mode=ParseMode.HTML)
    
    context.bot.send_message(text=constants.QUESTION_RECEIVED_MESSAGE,
                             chat_id=user.id,
                             parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END

def categories(update, context):
    """
    Allow user to choose amongst various volunteering categories.
    """
    logger.info('State: CHOICE - At categories...')

    query = update.callback_query
    update.answer_callback_query(query.id, text=query.data)
    
    # todo
    context.bot.send_message(text='This is not yet developed.',
                             chat_id=query.message.chat_id,
                             parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END

def cancel(update, context):
    """
    User cancelation function. Cancel conversation by user.
    """
    query = update.callback_query
    user = update.message.from_user
    logger.info("User {} canceled the conversation.".format(user.first_name))
    
    context.bot.send_message(text=constants.CANCEL_MESSAGE,
                             chat_id=query.message.chat_id,
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
            CHOICE: [CallbackQueryHandler('categories', pattern='^(categories)$'),
                     CallbackQueryHandler('question_intro', pattern='^(questions)$'),
                     CallbackQueryHandler('cancel', pattern='^(cancel)$')],
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