import constants 
import responses

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

logger.info('Bot started...')

def start_command(bot, update, context):
    # Send a message when the command /start is issued.
    update.message.reply_text(constants.START_MESSAGE)

def help_command(bot, update, context):
    # Send a message when the command /help is issued.
    update.message.reply_text(constants.HELP_MESSAGE)

def handle_message(bot, update, context):
    text = str(update.message.text).lower()
    response = responses.send_to_group(text)
    
    # Send whatever is sent to the bot to time to entrepret group
    bot.send_message(text=response,
                     chat_id=constants.TIME_TO_ENTREPRET)

    # update.message.reply_text(response)

def error(bot, update, context):
    # Log errors caused by updates
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(constants.API_KEY, use_context=True)
    
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