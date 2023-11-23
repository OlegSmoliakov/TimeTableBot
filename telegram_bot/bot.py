import telebot
from telebot import types

from key import token

bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start(chat):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton("Student")
    btn2 = types.KeyboardButton("Teacher")
    markup.row(btn1, btn2)
    bot.send_message(chat.chat.id, "Hello, choose your role", reply_markup=markup)
    bot.register_next_step_handler(chat, choose_role)


def choose_role(chat):
    if chat.text == "Student":
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton("Civil Engineering")
        btn2 = types.KeyboardButton("Power Engineering")
        markup.row(btn1, btn2)

        btn3 = types.KeyboardButton("Mining and Geology")
        btn4 = types.KeyboardButton("Chemical Technology and Metallurgy")
        markup.row(btn3, btn4)

        btn5 = types.KeyboardButton("Transportation and Mechanical Engineering")
        btn6 = types.KeyboardButton("Architecture, Urban Planning and Design")
        markup.row(btn5, btn6)

        btn7 = types.KeyboardButton("Law and international relations")
        btn8 = types.KeyboardButton("Informatics and Management Systems")
        markup.row(btn7, btn8)

        btn9 = types.KeyboardButton("Design International School")
        btn10 = types.KeyboardButton("Agricultural Science")
        markup.row(btn9, btn10)

        btn11 = types.KeyboardButton("Business Technology")
        btn12 = types.KeyboardButton(
            "Engineering Economic, Media Technologies and Social Sciences"
        )
        markup.row(btn11, btn12)

        btn13 = types.KeyboardButton("Sustainable Development of the Mountain")
        btn14 = types.KeyboardButton("Back")
        markup.row(btn13, btn14)

        bot.send_message(chat.chat.id, "Choose your faculty", reply_markup=markup)
        bot.register_next_step_handler(chat, choose_faculty)

    elif chat.text == "Teacher":
        bot.send_message(chat.chat.id, "Sorry, this option in progress")
        bot.register_next_step_handler(chat, choose_role)


def choose_faculty(chat):
    if chat.text == "Back":
        bot.register_next_step_handler(chat, start)


# def main(chat):
#    bot.send_message(chat.chat.id, f'Hello! {chat.from_user.first_name}')

bot.polling(none_stop=True)
