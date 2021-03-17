# SG Volunteer Handbook
## Introduction
This is a Telegram bot created for youths looking for volunteer opportunities but have limited knowledge/resources on how to do so. 
The Telegram bot is a handbook that allows youths to discover, learn and enquire about volunteering with their preferred communities.

## Roles
The bot supports 2 different roles:
* Volunteers: Those who would like to volunteer and are interested in finding out more. 
* Organisations: Organisations who have participated in providing information and replies any enquiries that Volunteers may have.

## Features
Most of the commands are available through the use of Inline Buttons by the Telegram Bot API. Users simply have to click on the available buttons to navigate through the Bot.
* `/start`: To start using the bot. All users/organisations will have to enter this to start using the bot.
* `/help`: To get the help page. This will show the commands the users can do.

### For Volunteers
#### See Categories
Volunteers can see the available volunteer communities to learn more about them. Under each community, there are various details such as:
* Introduction of Volunteer Community
* Do's and Dont's
* Organisations related to Volunteer Community

#### Learn about Organisations
When Volunteers click on the relevant Organisations under the Volunteer Communities, they will be able to learn more about the chosen Organisation. Details include:
* Type of Volunteers preferred
* Website link

#### Ask Question
Volunteers can ask questions, which will be directed to Organisations.

### For Organisations
After starting the bot with the `/start` command, Organisations will be able to reply questions asked by the Volunteers by simply using Telegram's reply function.

## Tech Stack used
* Heroku - Used to deploy the Telegram Bot
* Telegram - ...because it's a *Telegram* Bot
* PostgreSQL - Used with Heroku to store data in the cloud
