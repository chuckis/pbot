# bot.py

import os
import sqlite3
import webbrowser
import asyncio
import dotenv
from telegram import KeyboardButton, Update, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler

env = dotenv.dotenv_values()

TELEGRAM_TOKEN = env['TELEGRAM_TOKEN']

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (id INTEGER PRIMARY KEY, username TEXT, highscore INTEGER)''')
    conn.commit()
    conn.close()

# Проверка, существует ли игрок в базе данных
def player_exists(user_id):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM players WHERE id = ?', (user_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Функция для создания новой записи игрока
def create_player(user_id, username):
    if not player_exists(user_id):
        conn = sqlite3.connect('players.db')
        c = conn.cursor()
        c.execute('INSERT INTO players (id, username, highscore) VALUES (?, ?, ?)', (user_id, username, 0))
        conn.commit()
        conn.close()


# Функция для обновления рекорда
def update_highscore(user_id, new_score):
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    c.execute('UPDATE players SET highscore = ? WHERE id = ?', (new_score, user_id))
    conn.commit()
    conn.close()

# Команда /start
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    await update.message.reply_text(f'Привет, {user.first_name}! Давай начнем игру!')

    # Создаем пользователя в базе данных
    create_player(user.id, user.username)

    # Показать кнопку для запуска игры
    keyboard = [[KeyboardButton("Играть!", web_app=WebAppInfo(url="https://chuckis.github.io/flyingpoop/"))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Нажми кнопку для начала игры!', reply_markup=reply_markup)
    

# Запуск игры через веб-вью
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Запускаем веб-вью с игрой
    webbrowser.open(os.getenv('GAME_URL'))

    await query.answer()

# Команда для обновления рекорда
async def set_highscore(update: Update, context: CallbackContext):
    user = update.message.from_user
    score = int(context.args[0])
    
    update_highscore(user.id, score)
    await update.message.reply_text(f'Твой новый рекорд: {score} очков!')

# Обработка результата игры
async def handle_game_result(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user

    # Обрабатываем результат
    game_result = query.data  # Получаем данные от WebApp
    await query.answer()  # Закрываем запрос WebApp
    await update.message.reply_text(f"Ты набрал {game_result} очков!")
    
    # Обновляем рекорд в базе данных
    update_highscore(user.id, int(game_result))

# Основная функция запуска бота
def main():

    # Инициализация базы данных
    init_db()
    
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_highscore", set_highscore))
    application.add_handler(CallbackQueryHandler(handle_game_result))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main() # Запуск асинхронной функции через asyncio.run
