import constants

def send_to_group(text):
    return '<b>Someone asked this:</b> \n\n' + text

def reply_answer(question, reply):
    return '<b>Your reply to the question has been sent.</b> \nSee below for more information. \n\n<b>Question:</b> \n' + question + '\n\n<b>Your reply:</b> \n' + reply

def reply_to_user(question, reply):
    return '<b>GOOD NEWS! The organisation has replied to one of your questions.</b> \n\n<b>Your question:</b> \n' + question + '\n\n<b>Answer:</b> \n' + reply

def get_intro_text(community, about):
    return '<b>Community: </b>' + community + '\n\n<b>About Community: </b>\n' + about + '\n\n\nClick one of the options below to learn more about this community.'

def get_dos_n_donts(dos, donts):
    DO = ""
    DONT = ""
    for do in dos:
        DO += constants.BULLET_POINT + " " + do + "\n"
    for dont in donts:
        DONT += constants.BULLET_POINT + " " + dont + "\n"

    return "<b>Do's:</b> \n" + DO + "\n" +"<b>Dont's</b>: \n"+ DONT

def get_org_deets(org_deets):
    return "<b>Organisation: </b>" + org_deets["Organisation"] + "\n\n<b>About: </b>" + org_deets["About_Organisation"]