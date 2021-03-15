import os

# For connection
API_KEY = '1685534914:AAHnkhAmCBwvsP7oiYKcA6gnTpsHsdWC9DA'
APP_NAME = 'https://hackforgood2021.herokuapp.com/'
PORT = int(os.environ.get('PORT', 5000))

# Organisation IDs
TEST = '-560294536'
TIME_TO_ENTREPRET = '-432918969'
APPROVED_ORGANISATIONS = [TIME_TO_ENTREPRET, TEST]

# Symbols
BULLET_POINT = '&#8226'

# Messages
START_MESSAGE = 'Hello! Welcome to the Volunteer Handbook. Here, you can ask questions or explore our libraries for information on volunteering at various organisations. \n\n Currently, this bot supports: \n' + BULLET_POINT + ' Sending questions to the adminstrators'
START_MESSAGE_ORG = 'Hello! In this chat you can reply to questions sent. Just reply to the message when I send you a question!'
CANCEL_MESSAGE = 'Goodbye! Hope you\'ve learnt more about volunteering :) \n\n Send /start if you would like to start another conversation.'
HELP_MESSAGE = 'Here is a list of commands that you can do: \n\n /start : Start browsing! \n /help : Use this to get help!'
QUESTION_MESSAGE = 'Send your question below.'
QUESTION_RECEIVED_MESSAGE = 'Question sent. The organisers will get back to you when they can! You can ask another question or end the conversation by clicking on Cancel.'
REPLY_RECEIVED_MESSAGE = 'Reply sent to user.'
INVALID_REPLY = 'This is an invalid message to reply to!'