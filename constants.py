import os

# For connection
API_KEY = '1685534914:AAHnkhAmCBwvsP7oiYKcA6gnTpsHsdWC9DA'
APP_NAME = 'https://hackforgood2021.herokuapp.com/'
PORT = int(os.environ.get('PORT', 5000))

# Folder
DATA_FOLDER = './Data'
CATEGORIES_FOLDER = './Data/Categories'
ORGANISATIONS_FOLDER = './Data/Organisations'

# Organisation IDs
TEST = '-560294536'
TIME_TO_ENTREPRET = '-432918969'
APPROVED_ORGANISATIONS = [TIME_TO_ENTREPRET, TEST]

# Details
CATEGORY_DETAILS = ["Do's and Dont's", "Organisations"]
ORGANISATION_DETAILS = ["Volunteers Needed", "Go to Website"]

# Symbols
BULLET_POINT = '&#8226'

# Messages
START_MESSAGE = 'Hello! Welcome to the Volunteer Guidebot! Here, you can ask questions or explore our libraries for information on volunteering at various organisations. \n\n Currently, this bot supports: \n' + BULLET_POINT + ' Sending questions to the adminstrators'
START_MESSAGE_ORG = 'Hello! In this chat you can reply to questions sent. Just reply to the message when I send you a question!'
CANCEL_MESSAGE = 'Goodbye! Hope you\'ve learnt more about volunteering :) \n\nSend /start if you would like to start another conversation.'
HELP_MESSAGE = 'Who are we? \n\nThis Volunteer Guidebot is a personalized one-stop handbook chatbot that allows you to discover, learn, and enquire about volunteering with various communities in Singapore. \n\nHere is a list of commands that you can do: \n\n /start: Start browsing! \n /help: Use this to get help. \n /cancel: Quit the bot. See you again!'
QUESTION_MESSAGE = 'Please send your question below. Your question will be forwarded to the organisations for follow up. \n\nIf you would like to go back, click on the Back. \n\nIf you would like to cancel the conversation, click on Cancel.'
QUESTION_RECEIVED_MESSAGE = 'Question sent. The organisations will get back to you when they can! You can ask another question or end the conversation by clicking on Cancel.'
REPLY_RECEIVED_MESSAGE = 'Reply sent to user.'
INVALID_REPLY = 'Oops! I didn\'t catch that. See /help for what you can do.'
CATEGORIES_MESSAGE = 'Which community do you want to know more about?'
ORGANISATION_MESSAGE = 'Which organisation do you want to know more about?'
ORGANISATION_DETAIL_MESSAGE = "What do you want to know more about?"

ERROR_MESSAGE = 'An error occurred. Please send /start to restart the conversation.'