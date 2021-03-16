import os
import html
import json
import logging
import psycopg2

import constants 
import responses
import Data
import Data.Categories as Categories

from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters

# Set states
START, CHOICE, ORGANISATION, QUESTION, REPLY, CATEGORIES, DETAILS = range(7)

# Callback data
CATEGORY, QUESTIONS, REPLY, CANCEL, BACK = range(5)

# TEMP STORE
DATA = {}
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
    CURRENT["state"] = START

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
    CURRENT["state"] = CHOICE

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
    CURRENT["state"] = QUESTION

    user = update.message.from_user
    text = update.message.text
    
    response = responses.send_to_group(text)
    
    button_list = [[InlineKeyboardButton(text='Back', callback_data=str(BACK))],
                   [InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))]]
    keyboard = InlineKeyboardMarkup(button_list)
    
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
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)

def reply_question(update, context):
    """
    Allow organisations to reply questions.
    """
    logger.info('State: ORGANISATION - Replying...')
    CURRENT["state"] = ORGANISATION

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
    CURRENT["state"] = CHOICE

    query = update.callback_query
    context.bot.answer_callback_query(query.id, text=query.data)
    
    button_list = []

    for category in DATA["list_categories"]:
        button_list.append([InlineKeyboardButton(text=category, callback_data=category)])
    
    button_list.append([InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)
    
    context.bot.send_message(text=constants.CATEGORIES_MESSAGE,
                             chat_id=query.message.chat_id,
                             reply_markup = keyboard,
                             parse_mode=ParseMode.HTML)
    
    return CATEGORIES

def show_category(update, context):
    """
    Show the chosen category
    """
    query = update.callback_query

    logger.info("User clicked on category {}".format(query.data))
    
    CURRENT["state"] = CATEGORIES
    CURRENT["category"] = query.data
    
    button_list = []
    for detail in constants.CATEGORY_DETAILS:
        button_list.append([InlineKeyboardButton(text=detail, callback_data=detail)])
    button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
    button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)

    about = ""    
    for key in DATA["categories"]:
        if DATA["categories"][key]["Community"] == query.data:
            about = DATA["categories"][key]["About_Community"]
    intro_text = responses.get_intro_text(query.data, about)
    
    context.bot.send_message(text=intro_text,
                             chat_id=query.message.chat_id,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)
    
    return DETAILS

def category_detail(update, context):
    """
    Show the information requested by user
    """
    CURRENT["state"] = DETAILS
    
    #todo

    query = update.callback_query
    
    context.bot.send_message(text=query.data,
                             chat_id=query.message.chat_id,
                             parse_mode=ParseMode.HTML)
    
def back(update, context):
    if CURRENT["state"] == QUESTION:
        # Show choice menu
        start(update, context)
        return CHOICE
    #todo
    return

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
    
    categories_handler = []
    for category in DATA["list_categories"]:
        categories_handler.append(CallbackQueryHandler(show_category, pattern='^' + category + '$'))
    categories_handler.append(CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'))
    categories_handler.append(CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$'))

    details_handler = []
    for detail in constants.CATEGORY_DETAILS:
        details_handler.append(CallbackQueryHandler(category_detail, pattern='^' + detail + '$'))
    details_handler.append(CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'))
    details_handler.append(CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$'))
    
    # Add conversation handler with predefined states:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOICE: [CallbackQueryHandler(categories, pattern='^' + str(CATEGORY) + '$'),
                     CallbackQueryHandler(ask_question_intro, pattern='^' + str(QUESTIONS) + '$'),
                     CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            QUESTION: [MessageHandler(Filters.text, ask_question),
                       CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'),
                       CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            CATEGORIES: categories_handler,
            DETAILS: details_handler,
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
    
def load_files():
    logger.info('Loading json files from Data...')
    categories = os.listdir(constants.CATEGORIES_FOLDER)
    categories.sort()
    
    DATA["list_categories"] = []
    DATA["categories"] = {}
    
    for category in categories:
        file_name = category.split('.')[0]
        file = open(os.path.join(constants.CATEGORIES_FOLDER, category))
        DATA["categories"][file_name] = json.load(file)
        DATA["list_categories"].append(DATA["categories"][file_name]["Community"])
        
    organisations = os.listdir(constants.ORGANISATIONS_FOLDER)
    organisations.sort()
    
    DATA["list_organisations"] = []
    DATA["organisations"] = {}
    
    for organisation in organisations:
        file_name = organisation.split('.')[0]
        file = open(os.path.join(constants.ORGANISATIONS_FOLDER, organisation))
        DATA["organisations"][file_name] = json.load(file)
        DATA["list_organisations"].append(DATA["organisations"][file_name]["Organisation"])
            
def connect_PSQL():
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
        
def close_PSQL():
    try:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed.")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.warning(error)

if __name__ == '__main__':
    load_files()
    connect_PSQL()
    main()
    close_PSQL()