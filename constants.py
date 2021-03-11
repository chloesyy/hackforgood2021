import os

# For connection
API_KEY = '1685534914:AAHnkhAmCBwvsP7oiYKcA6gnTpsHsdWC9DA'
APP_NAME = 'https://hackforgood2021.herokuapp.com/'
PORT = int(os.environ.get('PORT', 5000))

# Organisation IDs
TIME_TO_ENTREPRET = '-432918969'

# Symbols
BULLET_POINT = '&#8226'

# Messages
START_MESSAGE = 'Hello! Welcome to the Volunteer Handbook. Here, you can ask questions or explore our libraries for information on volunteering at various organisations. \n\n Currently, this bot supports: \n' + BULLET_POINT + ' Sending questions to the adminstrators'
HELP_MESSAGE = 'Here is a list of commands that you can do: \n\n /start : Start browsing! \n /help : Use this to get help!'