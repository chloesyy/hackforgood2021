import os
import html
import logging
import psycopg2

import constants 
import responses

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters

# Set states
CHOICE, ORGANISATION, QUESTION, REPLY, CATEGORIES = range(5)

# Callback data
CATEGORY, QUESTIONS, REPLY, CANCEL = range(4)

# TEMP STORE
CURRENT = {}

# Define psql connectors
conn = None
cur = None

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
    
    # Check if chat_id is an organisation
    if str(update.message.chat.id) in constants.APPROVED_ORGANISATIONS:
        context.bot.send_message(text=constants.START_MESSAGE_ORG,
                                 chat_id=update.message.chat.id,
                                 parse_mode=ParseMode.HTML)
        return ORGANISATION
    
    button_list = [[InlineKeyboardButton(text='See Categories', callback_data=str(CATEGORY))],
                   [InlineKeyboardButton(text='Ask Questions', callback_data=str(QUESTIONS))],
                   [InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))]]
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

def ask_question_intro(update, context):
    """
    Question intro line
    """
    logger.info('State: CHOICE - Waiting for question...')

    query = update.callback_query
    context.bot.answer_callback_query(query.id, text=query.data)
    
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
    text = update.message.text
    
    response = responses.send_to_group(text)
    
    user_button_list = [[InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))]]
    user_keyboard = InlineKeyboardMarkup(user_button_list)
    
    # Send whatever is sent to the bot to time to entrepret group
    sentMessage = context.bot.send_message(text=response,
                     chat_id=constants.TEST,
                     parse_mode=ParseMode.HTML)
    
    message_id = sentMessage.message_id

    # Insert question into database
    cur.execute(f"INSERT INTO questions(message_id, user_id, question) VALUES ({message_id}, {user.id}, '{text}');")
    conn.commit()
    logger.info('Question inserted into database.')

    # Send acknowledgement to user
    context.bot.send_message(text=constants.QUESTION_RECEIVED_MESSAGE,
                             chat_id=user.id,
                             reply_markup=user_keyboard,
                             parse_mode=ParseMode.HTML)

def reply_question(update, context):
    """
    Allow organisations to reply questions.
    """
    logger.info('State: ORGANISATION - Replying...')

    text = update.message.text
    message_id = update.message.reply_to_message.message_id

     # Result is message_id, user_id, question, organisation
    cur.execute(f"SELECT * FROM questions WHERE message_id = '{message_id}';")
    result = cur.fetchall()

    if len(result) == 0 and update.message.reply_to_message.from_user.is_bot is True:
        reply_to_message_id = update.message.message_id
        context.bot.send_message(text=constants.INVALID_REPLY,
                                 reply_to_message_id=reply_to_message_id,
                                 chat_id=constants.TEST,
                                 parse_mode=ParseMode.HTML)
        return

    # Setup current reply details
    CURRENT["user"] = result[0][1]
    CURRENT["question"] = result[0][2]
    
    acknowledgement = responses.reply_answer(CURRENT["question"], text)
    touser = responses.reply_to_user(CURRENT["question"], text)
    
    context.bot.send_message(text=acknowledgement,
                             chat_id=constants.TEST, 
                             parse_mode=ParseMode.HTML)

    context.bot.send_message(text=touser,
                             chat_id=CURRENT["user"],
                             parse_mode=ParseMode.HTML)  

def categories(update, context):
    """
    Allow user to choose amongst various volunteering categories.
    """
    logger.info('State: CHOICE - Showing categories...')

    query = update.callback_query
    context.bot.answer_callback_query(query.id, text=query.data)
    
    # todo
    context.bot.send_message(text='This is not yet developed. The conversation has ended. Send /start to start the conversation again.',
                             chat_id=query.message.chat_id,
                             parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END

def cancel(update, context):
    """
    User cancelation function. Cancel conversation by user.
    """
    query = update.callback_query
    context.bot.answer_callback_query(query.id, text=query.data)

    user = query.from_user
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
            CHOICE: [CallbackQueryHandler(categories, pattern='^' + str(CATEGORY) + '$'),
                     CallbackQueryHandler(ask_question_intro, pattern='^' + str(QUESTIONS) + '$'),
                     CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            QUESTION: [MessageHandler(Filters.text, ask_question),
                       CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            ORGANISATION: [MessageHandler(Filters.text, reply_question)]
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
    
def connectPSQL():
    try:
        logger.info("Connecting to PSQL...")
        DATABASE_URL = os.environ['DATABASE_URL']
        global conn
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        global cur
        cur = conn.cursor()
        logger.info("Connected to PSQL.")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.warning(error)
        
def closePSQL():
    try:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed.")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.warning(error)

if __name__ == '__main__':
    connectPSQL()
    main()
    closePSQL()