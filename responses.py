def send_to_group(text):
    return '<b>Someone asked this:</b> \n\n' + text

def reply_from_group(text):
    return '<b>You are replying to:</b> \n\n' + text + '\n\n Please send your reply below.'

def reply_answer(question, reply):
    return '<b>You replied:</b> \n' + reply + '\n\n <b>To question:</b> \n' + question

def reply_to_user(question, reply):
    return '<b>In reply to:</b> \n' + question + '\n\n <b>Reply:</b> \n' + reply