import time
import telebot
import random
import sqlite3
from threading import Thread
from flask import Flask

# ===== ФЛASK ДЛЯ RENDER (ЧТОБЫ БЫЛ ПОРТ) =====
app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

Thread(target=run_flask).start()

# ===== ТОКЕН И АДМИНЫ =====
TOKEN = '8848646166:AAGtIokIDI-kS7ANW0ZOyjUjppNrDp0iS5w'  # ВСТАВЬ СВОЙ ТОКЕН!
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [7712380726]  # ЗАМЕНИ НА СВОЙ ID!

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            last_work_time INTEGER DEFAULT 0,
            username TEXT DEFAULT '',
            daily_bonus_time INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            games_lost INTEGER DEFAULT 0,
            registered_at INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            amount INTEGER,
            timestamp INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id, username=None):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT balance, last_work_time, username, daily_bonus_time,
               games_played, games_won, games_lost, registered_at
        FROM users WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        if username and result[2] != username:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
            conn.commit()
            conn.close()
        return {
            'balance': result[0],
            'last_work_time': result[1],
            'username': result[2] or username or '',
            'daily_bonus_time': result[3] or 0,
            'games_played': result[4] or 0,
            'games_won': result[5] or 0,
            'games_lost': result[6] or 0,
            'registered_at': result[7] or 0
        }
    else:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users
            (user_id, balance, last_work_time, username, daily_bonus_time,
             games_played, games_won, games_lost, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 0, 0, username or '', 0, 0, 0, 0, int(time.time())))
        conn.commit()
        conn.close()
        return {
            'balance': 0,
            'last_work_time': 0,
            'username': username or '',
            'daily_bonus_time': 0,
            'games_played': 0,
            'games_won': 0,
            'games_lost': 0,
            'registered_at': int(time.time())
        }

def update_balance(user_id, new_balance):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    conn.close()

def update_work_time(user_id, work_time):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_work_time = ? WHERE user_id = ?', (work_time, user_id))
    conn.commit()
    conn.close()

def update_daily_bonus(user_id, bonus_time):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET daily_bonus_time = ? WHERE user_id = ?', (bonus_time, user_id))
    conn.commit()
    conn.close()

def update_stats(user_id, won=False, lost=False):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
    if won:
        cursor.execute('UPDATE users SET games_won = games_won + 1 WHERE user_id = ?', (user_id,))
    if lost:
        cursor.execute('UPDATE users SET games_lost = games_lost + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_history(user_id, action, amount):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO history (user_id, action, amount, timestamp) VALUES (?, ?, ?, ?)',
                   (user_id, action, amount, int(time.time())))
    conn.commit()
    conn.close()

def get_total_earned(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM history WHERE user_id = ? AND amount > 0', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] else 0

def find_user_by_username(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def find_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

init_db()

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    user = get_user(user_id, username)

    bot.reply_to(message, f"🎰 Добро пожаловать в казино!\n"
                          f"💰 Ваш баланс: {user['balance']} монет\n\n"
                          f"Доступные команды:\n"
                          f"/work - работа (30 мин)\n"
                          f"/casino [сумма] - казино\n"
                          f"/coin [сумма] [орел/решка] - монетка\n"
                          f"/daily - ежедневный бонус\n"
                          f"/give [@username] [сумма] - подарить\n"
                          f"/profile - мой профиль\n"
                          f"/stats - статистика\n"
                          f"/balance - баланс\n"
                          f"/top - топ игроков\n"
                          f"/help - помощь")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "🎲 Доступные команды:\n\n"
                          "💰 ЭКОНОМИКА:\n/work - работа (20-60 монет, раз в 30 мин)\n"
                          "/daily - ежедневный бонус (200-300 монет)\n"
                          "/give [@username] [сумма] - подарить монеты\n"
                          "/balance - баланс\n"
                          "/top - топ игроков\n\n"
                          "🎲 ИГРЫ:\n/casino [сумма] - казино (ставка 50-1000)\n"
                          "/coin [сумма] [орел/решка] - монетка\n\n"
                          "📊 ПРОФИЛЬ:\n/profile - мой профиль\n"
                          "/stats - статистика игр\n\n"
                          "👑 АДМИН:\n/addmoney [@username] [сумма]\n/removemoney [@username] [сумма]")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    bot.reply_to(message, f"💰 Ваш баланс: {user['balance']} монет")

@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or 'Нет юзернейма'
    first_name = message.from_user.first_name or 'Нет имени'
    user = get_user(user_id, username)
    total_earned = get_total_earned(user_id)
    
    if user['registered_at'] > 0:
        reg_date = time.strftime('%d.%m.%Y %H:%M', time.localtime(user['registered_at']))
    else:
        reg_date = 'Неизвестно'
    
    bot.reply_to(message, f"👤 ВАШ ПРОФИЛЬ:\n\n"
                          f"🆔 ID: {user_id}\n"
                          f"📛 Имя: {first_name}\n"
                          f"🔹 Юзернейм: @{username}\n"
                          f"📅 Регистрация: {reg_date}\n"
                          f"💰 Баланс: {user['balance']} монет\n"
                          f"💵 Всего заработано: {total_earned} монет\n"
                          f"🎮 Сыграно игр: {user['games_played']}\n"
                          f"🏆 Побед: {user['games_won']}\n"
                          f"💀 Поражений: {user['games_lost']}")

@bot.message_handler(commands=['work'])
def work_command(message):
    user_id = message.from_user.id
    current_time = int(time.time())
    username = message.from_user.username or ''
    user = get_user(user_id, username)

    if user['last_work_time'] > 0 and current_time - user['last_work_time'] < 1800:
        remaining = int(1800 - (current_time - user['last_work_time']))
        minutes = remaining // 60
        seconds = remaining % 60
        bot.reply_to(message, f"⏳ Подождите {minutes} мин {seconds} сек до следующей работы!")
        return

    salary = random.randint(20, 60)
    new_balance = user['balance'] + salary
    update_balance(user_id, new_balance)
    update_work_time(user_id, current_time)
    add_history(user_id, "Работа", salary)

    bot.reply_to(message, f"💼 Вы отработали смену и получили {salary} монет!\n💰 Баланс: {new_balance} монет")

@bot.message_handler(commands=['casino'])
def casino_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    user = get_user(user_id, username)
    balance = user['balance']

    parts = message.text.split()
    if len(parts) == 1:
        bot.reply_to(message, "❌ Укажите сумму ставки!\nПример: /casino 374")
        return

    try:
        bet = int(parts[1])
    except:
        bot.reply_to(message, "❌ Введите число!\nПример: /casino 374")
        return

    if bet < 50:
        bot.reply_to(message, "❌ Минимальная ставка: 50 монет!")
        return

    if bet > 1000:
        bot.reply_to(message, "❌ Максимальная ставка: 1000 монет!")
        return

    if bet > balance:
        bot.reply_to(message, f"❌ Недостаточно монет! У вас {balance} монет.")
        return

    outcomes = [
        {'text': '🍒 Вишня', 'multiplier': 0},
        {'text': '🍋 Лимон', 'multiplier': 0.5},
        {'text': '🍊 Апельсин', 'multiplier': 1},
        {'text': '🍇 Виноград', 'multiplier': 2},
        {'text': '💎 ДЖЕКПОТ!', 'multiplier': 5}
    ]

    result = random.choice(outcomes)
    win = int(bet * result['multiplier'])
    new_balance = balance - bet + win
    update_balance(user_id, new_balance)

    if win == 0:
        msg = f"😵 Выпало: {result['text']}\n❌ Вы проиграли {bet} монет!"
        update_stats(user_id, lost=True)
    elif win == bet:
        msg = f"🔄 Выпало: {result['text']}\n✅ Вы вернули ставку!"
    elif win > bet:
        msg = f"🎉 Выпало: {result['text']}\n🔥 Вы выиграли {win} монет! (x{result['multiplier']})"
        update_stats(user_id, won=True)
    else:
        msg = f"😅 Выпало: {result['text']}\n💰 Вы вернули {win} монет (частичный возврат)"
        update_stats(user_id, lost=True)

    msg += f"\n💰 Новый баланс: {new_balance} монет"
    bot.reply_to(message, msg)
    add_history(user_id, "Казино", win - bet)

@bot.message_handler(commands=['coin'])
def coin_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    user = get_user(user_id, username)
    balance = user['balance']

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /coin [сумма] [орел/решка]")
        return

    try:
        bet = int(parts[1])
    except:
        bot.reply_to(message, "❌ Сумма должна быть числом!")
        return

    if bet < 10:
        bot.reply_to(message, "❌ Минимальная ставка: 10 монет!")
        return

    if bet > balance:
        bot.reply_to(message, f"❌ Недостаточно монет! У вас {balance} монет.")
        return

    choice = parts[2].lower()
    if choice not in ['орел', 'решка']:
        bot.reply_to(message, "❌ Выберите: орел или решка")
        return

    result = random.choice(['орел', 'решка'])
    win = bet * 2 if choice == result else 0

    if win > 0:
        new_balance = balance + bet
        update_balance(user_id, new_balance)
        update_stats(user_id, won=True)
        bot.reply_to(message, f"🪙 Выпало: {result}!\n🎉 Вы выиграли {bet} монет!\n💰 Новый баланс: {new_balance}")
        add_history(user_id, "Орел/Решка", bet)
    else:
        new_balance = balance - bet
        update_balance(user_id, new_balance)
        update_stats(user_id, lost=True)
        bot.reply_to(message, f"🪙 Выпало: {result}!\n😵 Вы проиграли {bet} монет!\n💰 Новый баланс: {new_balance}")
        add_history(user_id, "Орел/Решка", -bet)

@bot.message_handler(commands=['daily'])
def daily_command(message):
    user_id = message.from_user.id
    current_time = int(time.time())
    username = message.from_user.username or ''
    user = get_user(user_id, username)

    if user['daily_bonus_time'] > 0 and current_time - user['daily_bonus_time'] < 86400:
        remaining = int(86400 - (current_time - user['daily_bonus_time']))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        bot.reply_to(message, f"⏳ Ежедневный бонус уже получен! Следующий через {hours} ч {minutes} мин.")
        return

    bonus = random.randint(200, 300)
    new_balance = user['balance'] + bonus
    update_balance(user_id, new_balance)
    update_daily_bonus(user_id, current_time)
    add_history(user_id, "Ежедневный бонус", bonus)

    bot.reply_to(message, f"🎁 Вы получили ежедневный бонус {bonus} монет!\n💰 Баланс: {new_balance} монет")

@bot.message_handler(commands=['give'])
def give_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    user = get_user(user_id, username)
    balance = user['balance']

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /give [@username] [сумма]")
        return

    target = parts[1]
    try:
        amount = int(parts[2])
    except:
        bot.reply_to(message, "❌ Сумма должна быть числом!")
        return

    if amount < 1:
        bot.reply_to(message, "❌ Сумма должна быть больше 0!")
        return

    if amount > balance:
        bot.reply_to(message, f"❌ Недостаточно монет! У вас {balance} монет.")
        return

    if target.startswith('@'):
        result = find_user_by_username(target[1:])
        if not result:
            bot.reply_to(message, "❌ Пользователь не найден!")
            return
        target_id = result[0]
    else:
        try:
            target_id = int(target)
            result = find_user_by_id(target_id)
            if not result:
                bot.reply_to(message, "❌ Пользователь не найден!")
                return
        except:
            bot.reply_to(message, "❌ Некорректный ID!")
            return

    if target_id == user_id:
        bot.reply_to(message, "❌ Нельзя подарить самому себе!")
        return

    update_balance(user_id, balance - amount)
    target_user = get_user(target_id)
    update_balance(target_id, target_user['balance'] + amount)

    add_history(user_id, "Подарок", -amount)
    add_history(target_id, "Получено", amount)

    bot.reply_to(message, f"✅ Вы подарили {amount} монет пользователю {target}\n💰 Новый баланс: {balance - amount}")

    try:
        bot.send_message(target_id, f"🎁 Вы получили {amount} монет от {message.from_user.first_name}!\n💰 Ваш баланс: {target_user['balance'] + amount}")
    except:
        pass

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or ''
    user = get_user(user_id, username)

    bot.reply_to(message, f"📊 ВАША СТАТИСТИКА:\n\n"
                          f"🔄 Сыграно игр: {user['games_played']}\n"
                          f"🏆 Побед: {user['games_won']}\n"
                          f"💀 Поражений: {user['games_lost']}\n"
                          f"📈 Процент побед: {int(user['games_won'] / max(1, user['games_played']) * 100)}%\n"
                          f"💰 Баланс: {user['balance']} монет")

@bot.message_handler(commands=['top'])
def top_command(message):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, balance, username FROM users ORDER BY balance DESC LIMIT 5')
    results = cursor.fetchall()
    conn.close()

    if not results:
        bot.reply_to(message, "📊 Пока нет игроков!")
        return

    top_text = "🏆 ТОП ИГРОКОВ:\n\n"
    for i, (user_id, balance, username) in enumerate(results, 1):
        name = f"@{username}" if username else f"ID{user_id}"
        top_text += f"{i}. {name} — {balance} монет\n"

    bot.reply_to(message, top_text)

# ===== АДМИН-КОМАНДЫ =====
@bot.message_handler(commands=['addmoney'])
def add_money(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Нет прав!")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /addmoney [@username или ID] [сумма]")
        return

    target = parts[1]
    try:
        amount = int(parts[2])
    except:
        bot.reply_to(message, "❌ Сумма должна быть числом!")
        return

    target_id = None
    target_name = ""

    if target.startswith('@'):
        result = find_user_by_username(target[1:])
        if result:
            target_id = result[0]
            target_name = target
        else:
            try:
                chat = bot.get_chat(target)
                target_id = chat.id
                target_name = target
                get_user(target_id, target[1:])
            except:
                bot.reply_to(message, "❌ Пользователь не найден!")
                return
    else:
        try:
            target_id = int(target)
            user = get_user(target_id)
            target_name = f"@{user['username']}" if user['username'] else target
        except:
            bot.reply_to(message, "❌ Пользователь не найден!")
            return

    user = get_user(target_id)
    new_balance = user['balance'] + amount
    update_balance(target_id, new_balance)
    add_history(target_id, "Админ пополнение", amount)

    bot.reply_to(message, f"✅ Добавлено {amount} монет игроку {target_name}!\n💰 Новый баланс: {new_balance}")

    try:
        bot.send_message(target_id, f"💰 Вам начислено {amount} монет! Ваш баланс: {new_balance}")
    except:
        pass

@bot.message_handler(commands=['removemoney'])
def remove_money(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Нет прав!")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /removemoney [@username или ID] [сумма]")
        return

    target = parts[1]
    try:
        amount = int(parts[2])
    except:
        bot.reply_to(message, "❌ Сумма должна быть числом!")
        return

    if amount < 0:
        bot.reply_to(message, "❌ Сумма должна быть положительной!")
        return

    target_id = None
    target_name = ""

    if target.startswith('@'):
        result = find_user_by_username(target[1:])
        if result:
            target_id = result[0]
            target_name = target
        else:
            try:
                chat = bot.get_chat(target)
                target_id = chat.id
                target_name = target
                get_user(target_id, target[1:])
            except:
                bot.reply_to(message, "❌ Пользователь не найден!")
                return
    else:
        try:
            target_id = int(target)
            user = get_user(target_id)
            target_name = f"@{user['username']}" if user['username'] else target
        exce
