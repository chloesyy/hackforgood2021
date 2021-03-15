def send_to_group(text):
    return '<b>Someone asked this:</b> \n\n' + text

def reply_answer(question, reply):
    return '<b>Your reply to the question has been sent.</b> \nSee below for more information. \n\n<b>Question:</b> \n' + question + '\n\n<b>Your reply:</b> \n' + reply

def reply_to_user(question, reply):
    return '<b>GOOD NEWS! The organisation has replied to one of your questions.</b> \n\n<b>Your question:</b> \n' + question + '\n\n<b>Answer:</b> \n' + reply