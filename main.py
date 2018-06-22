import config
import telebot
import qna
import db
import os
from flask import Flask, request


TOKEN = config.token
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
isgamestarted = None
players = []
gamestatus = 'The game hasn\'t started yet.'
try:
    isgamestarted = db.get_game_status()
    players = db.get_ids()
except Exception as e:
    print(e)


@bot.message_handler(commands=['start'])
def start(message):
    try:
        global isgamestarted
        global players
        isinbase = db.add_player(message.from_user.id, message.from_user.username,
                                 message.from_user.first_name, message.from_user.last_name)
        if isinbase:
            response = 'You already registered.\n*/rules* - Rules.'
        else:
            response = 'Hola, thanks for registration!\n*/rules* - Rules.'
            players.append(message.from_user.id)
        if isgamestarted:
            response += '\n\n_The game is going!_'
        else:
            response += '\n\n_The game will begin soon._'
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Oh, exception :(')


@bot.message_handler(commands=['rules'])
def rules(message):
    response = 'Commands: ...\nHow to: ...'
    if not isgamestarted:
        response += '\nThe game will begin soon.'
    bot.send_message(message.chat.id, response, parse_mode='Markdown')


@bot.message_handler(commands=['iwannathescores'])
def scores(message):
    try:
        response = db.players_to_list(db.get_players())
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Oh-oh, exception :(')


@bot.message_handler(commands=['iwannathescorestoall'])
def scores_to_all(message):
    try:
        global players
        response = db.players_to_list(db.get_players())
        bot.send_message(message.chat.id, 'Sending the results.')
        for id in players:
            bot.send_message(id, response, parse_mode='Markdown')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Oba, exception :(')


@bot.message_handler(commands=['iwannathegametostart'])
def start_game(message):
    try:
        global isgamestarted
        global players
        if isgamestarted is False:
            isgamestarted = True
            db.set_game_status(True)
            bot.send_message(message.chat.id, 'I start the game.')
            for id in players:
                bot.send_message(id, '_Game started!_', parse_mode='Markdown')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Exception :(')


@bot.message_handler(commands=['iwannathegametostop'])
def stop_game(message):
    try:
        global isgamestarted
        global gamestatus
        global players
        if isgamestarted is True:
            isgamestarted = False
            db.set_game_status(False)
            gamestatus = 'Game already over.'
            bot.send_message(message.chat.id, 'I finished the game.')
            for id in players:
                bot.send_message(id, '_Game over!_\nYou can\'t answer anymore.', parse_mode='Markdown')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Oh, exception :(')


@bot.message_handler(regexp='\A\d+ ')
def answer(message):
    try:
        global isgamestarted
        global players
        if message.from_user.id not in players:
            bot.send_message(message.chat.id, 'You didn\'t register.\n*/start* please.',
                             parse_mode='Markdown')
            return
        if isgamestarted is True:
            key, status, response = qna.check(message.text)
            if status is not None:
                isnotanswered = db.add_answer(message.from_user.id, key, message.date, status, message.text)
                if isnotanswered is True:
                    bot.send_message(message.chat.id, response, parse_mode='Markdown')
                elif isnotanswered is False:
                    bot.send_message(message.chat.id, 'You already answered this question.')
            else:
                bot.send_message(message.chat.id, response, parse_mode='Markdown')
        elif isgamestarted is False:
            bot.send_message(message.chat.id, gamestatus)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Exception :(')


@bot.message_handler(content_types=['text'])
def trash(message):
    global gamestatus
    response = 'I can\'t understand you.'
    if isgamestarted is False:
        response = gamestatus
    bot.send_message(message.chat.id, response)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=config.app_url + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
