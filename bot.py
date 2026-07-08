import telebot
import time

TOKEN = '8848646166:AAGtIokIDI-kS7ANW0ZOyjUjppNrDp0iS5w'  # Замени на свой токен!
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, '✅ Бот работает!')

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f'Вы написали: {message.text}')

while True:
    try:
        bot.infinity_polling()
    except:
        time.sleep(5)
