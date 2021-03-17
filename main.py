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
START, CHOICE, ORGANISATION, QUESTION, CATEGORIES, DETAILS, ORG_DEETS, VOLUNTEERS = range(8)

# Callback data
CATEGORY, QUESTIONS, CANCEL, BACK = range(4)

# TEMP STORE
DATA = {}
CURRENT = {}
CURRENT["state"] = None

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
    if CURRENT["state"] is not None:
        # To guard against users who send /start multiple times without cancelling conversation
        if update.callback_query is None:
            CURRENT["state"] = None
            context.bot.send_message(text=constants.ERROR_MESSAGE,
                                     chat_id=update.message.chat.id, 
                                     parse_mode=ParseMode.HTML)
            
            return ConversationHandler.END

        user = update.callback_query.message.chat
        chat_id = user
    else:
        user = update.message.from_user
        chat_id = update.message.chat.id
    
    logger.info('State: START')
    CURRENT["state"] = START
    
    # Check if chat_id is an organisation
    if str(chat_id) in constants.APPROVED_ORGANISATIONS:
        context.bot.send_message(text=constants.START_MESSAGE_ORG,
                                 chat_id=chat_id,
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
    
    button_list = [[InlineKeyboardButton(text='Back', callback_data=str(BACK))],
                   [InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))]]
    keyboard = InlineKeyboardMarkup(button_list)
    
    context.bot.send_message(text=constants.QUESTION_MESSAGE,
                             chat_id=query.message.chat_id,
                             reply_markup=keyboard,
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

# STATE: SHOWING ASK QUESTIONS/VIEW CATEGORIES
def categories(update, context):
    """
    Allow user to choose amongst various volunteering categories.
    """
    logger.info('State: CHOICE - Showing categories...')
    CURRENT["state"] = CHOICE

    query = update.callback_query
    
    button_list = []

    for category in DATA["list_categories"]: #these are all the categories(Disability) 
        button_list.append([InlineKeyboardButton(text=category, callback_data=category)]) #Creating the buttons to show each category
    button_list.append([InlineKeyboardButton(text='Back', callback_data=str(BACK))])
    button_list.append([InlineKeyboardButton(text='Cancel', callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)
    
    context.bot.send_message(text=constants.CATEGORIES_MESSAGE,
                             chat_id=query.message.chat_id,
                             reply_markup = keyboard,
                             parse_mode=ParseMode.HTML)
    
    return CATEGORIES

# STATE: DISPLAY ALL CATEGORIES/COMMUNITIES
def show_category(update, context):
    """
    Show the chosen category
    """
    query = update.callback_query

    if CURRENT["state"] != DETAILS: # If didn't press back button (natural flow)
        logger.info("User clicked on category {}".format(query.data))
        CURRENT["category"] = query.data
    
    CURRENT["state"] = CATEGORIES # Run this function with the current state = CATEGORIES

    button_list = []
    for detail in constants.CATEGORY_DETAILS: #these are all the categories of categories(Disability) i.e. the Dos and Donts
        button_list.append([InlineKeyboardButton(text=detail, callback_data=detail)]) #Creating each button to show each category
    button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
    button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)

    about = ""    
    for key in DATA["categories"]:
        if DATA["categories"][key]["Community"] == CURRENT["category"]:
            about = DATA["categories"][key]["About_Community"]
    intro_text = responses.get_intro_text(CURRENT["category"], about)
    
    context.bot.send_message(text=intro_text,
                             chat_id=query.message.chat_id,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)
    
    return DETAILS

# STATE: VIEWING CATEGORY/COMMUNITY DETAILS
def category_detail(update, context):
    """
    Show the information requested by user
    """
    query = update.callback_query
    new_state = None
    
    # Define temp store
    if CURRENT["state"] != ORG_DEETS:
        # Back button not pressed
        CURRENT["detail"] = query.data
    CURRENT["state"] = DETAILS

    logger.info("User clicked on {}".format(CURRENT["detail"]))
    # Dos and Donts
    if CURRENT["detail"] == constants.CATEGORY_DETAILS[0]:
        dos = []
        donts = []
        button_list=[]
        
        for key in DATA["categories"]:
            # If the current category is the same as the list of categories
            if DATA["categories"][key]["Community"] == CURRENT["category"]: 
                dos = DATA["categories"][key]["Dos_n_Donts"][0]
                donts = DATA["categories"][key]["Dos_n_Donts"][1]
                
        response = responses.get_dos_n_donts(dos, donts)
        
        button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
        button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
        keyboard = InlineKeyboardMarkup(button_list)

        context.bot.send_message(text=response,
                                 chat_id=query.message.chat_id,
                                 reply_markup=keyboard,
                                 parse_mode=ParseMode.HTML)

    # Organisations
    elif CURRENT["detail"] == constants.CATEGORY_DETAILS[1]:
        button_list = []
        for key in DATA["categories"]:
            if DATA["categories"][key]["Community"] == CURRENT["category"]:
                for o in DATA["categories"][key]["Organisations"]:
                    #Creating the button for the organization
                    button_list.append([InlineKeyboardButton(text=o, callback_data=o)]) 
        button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
        button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
        keyboard = InlineKeyboardMarkup(button_list)        

        context.bot.send_message(text=constants.ORGANISATION_MESSAGE,
                                 chat_id=query.message.chat_id,
                                 reply_markup=keyboard,
                                 parse_mode=ParseMode.HTML)
        new_state = ORG_DEETS

    else:
        context.bot.send_message(text="Error!",
                                 chat_id=query.message.chat_id,
                                 parse_mode=ParseMode.HTML)  
    
    return new_state

# STATE: VIEWING ORGANISATION DETAILS
def organisation_detail(update, context):
    """
    Shows users the details of the organisation.
    """
    query = update.callback_query
    
    CURRENT["state"] = ORG_DEETS
    CURRENT["organisation"] = query.data
    logger.info("User clicked on {}".format(CURRENT["organisation"]))

    organisation_deets = {}
    # Get details of organisation
    for key in DATA["organisations"]:
        if DATA["organisations"][key]["Organisation"] == CURRENT["organisation"]:
            organisation_deets = DATA["organisations"][key]

    response = responses.get_org_deets(organisation_deets)

    button_list = []
    for detail in constants.ORGANISATION_DETAILS: #these are all the categories of categories(Disability) i.e. the Dos and Donts
        if detail == "Go to Website":
            button_list.append([InlineKeyboardButton(text=detail, url=organisation_deets["Link"])])
        else:
            button_list.append([InlineKeyboardButton(text=detail, callback_data=detail)]) #Creating each button to show each category
    button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
    button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)
    context.bot.send_message(text=response,
                             chat_id=query.message.chat_id,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)
    
    return VOLUNTEERS

def volunteers(update, context):

    query = update.callback_query

    CURRENT["state"] = VOLUNTEERS
    CURRENT["org_deet"] = query.data
    logger.info("User clicked on {}".format(CURRENT["org_deet"]))

    volunteer_info = ""
    button_list=[]
    for key in DATA["organisations"]:
        if DATA["organisations"][key]["Organisation"] == CURRENT["organisation"]:
            for v in DATA["organisations"][key]["Volunteering_Roles"]:
                volunteer_info += constants.BULLET_POINT + " " + v + "\n"
    button_list.append([InlineKeyboardButton(text="Back", callback_data=str(BACK))])
    button_list.append([InlineKeyboardButton(text="Cancel", callback_data=str(CANCEL))])
    keyboard = InlineKeyboardMarkup(button_list)
    context.bot.send_message(text="<b>Volunteering Roles:</b> \n" + volunteer_info,
                             chat_id=query.message.chat_id,
                             reply_markup=keyboard,
                             parse_mode=ParseMode.HTML)

###----------------------------------------- BACK / CANCEL BUTTONS -----------------------------------------###

# BACK BUTTON
def back(update, context): 
    new_state = None # No new state
    if CURRENT["state"] == QUESTION or CURRENT["state"] == CHOICE:
        # Show choice menu
        logger.info("Going back to START")
        new_state = start(update, context)
    elif CURRENT["state"] == CATEGORIES:
        # Show categories
        logger.info("Going back to CHOICE")
        new_state = categories(update, context)
    elif CURRENT["state"] == DETAILS:
        # Show category details
        logger.info("Going back to CATEGORIES")
        new_state = show_category(update, context)
    elif CURRENT["state"] == ORG_DEETS:
        # Show details
        logger.info("Going back to DETAILS")
        new_state = category_detail(update,context)
    elif CURRENT["state"] == VOLUNTEERS:
        # Show organisation details
        logger.info("Going back to ORG_DEETS")
        new_state = organisation_detail(update,context)

    # Must return the previous state
    return new_state

# CANCEL BUTTON
def cancel(update, context):
    """
    User cancelation function. Cancel conversation by user.
    """
    query = update.callback_query
    if query is None:
        query = update
        user = update.message.from_user
    else:
        user = query.from_user

    logger.info("User {} canceled the conversation.".format(user.first_name))
    
    context.bot.send_message(text=constants.CANCEL_MESSAGE,
                             chat_id=query.message.chat_id,
                             parse_mode=ParseMode.HTML)
    
    # Need to redefine state here so that it does not interfere with back button
    CURRENT["state"] = None

    return ConversationHandler.END

# ERROR WARNING
def error(update, context):
    # Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, context.error)


###----------------------------------------- MAIN() -----------------------------------------###

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

    org_deets_handler = []
    for org in DATA["list_organisations"]:
        org_deets_handler.append(CallbackQueryHandler(organisation_detail, pattern='^' + org + '$'))
    org_deets_handler.append(CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'))
    org_deets_handler.append(CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$'))
    
    # Add conversation handler with predefined states:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOICE: [CallbackQueryHandler(categories, pattern='^' + str(CATEGORY) + '$'),
                     CallbackQueryHandler(ask_question_intro, pattern='^' + str(QUESTIONS) + '$'),
                     CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'),
                     CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            QUESTION: [MessageHandler(Filters.text, ask_question),
                       CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'),
                       CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$')],
            CATEGORIES: categories_handler,
            DETAILS: details_handler,
            ORG_DEETS: org_deets_handler,
            VOLUNTEERS: [CallbackQueryHandler(volunteers, pattern='^' + constants.ORGANISATION_DETAILS[0] + '$'), 
                            CallbackQueryHandler(back, pattern='^' + str(BACK) + '$'),
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
    
###----------------------------------------- CONNECTING TO DATABASE -----------------------------------------###

# LOAD .JSON FILES WITH TEXT DETAILS
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

# CLOSE CONNECTION TO HEROKU        
def close_PSQL():
    try:
        if conn is not None:
            conn.close()
            logger.info("Database connection closed.")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.warning(error)

###----------------------------------------- END -----------------------------------------###

if __name__ == '__main__':
    load_files()
    connect_PSQL()
    main()
    close_PSQL()