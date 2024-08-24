# bot.py

import sqlite3
import dotenv
import json
import logging

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(f'Привет, {user.first_name}! Давай начнем игру!')

    create_player(user.id, user.username)

    # Показать кнопку для запуска игры
    keyboard = [[KeyboardButton("Играть!", web_app=WebAppInfo(url="https://chuckis.github.io/flyingpoop/"))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Нажми кнопку для начала игры!', reply_markup=reply_markup)
    
# Handle incoming WebAppData
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Print the received data and remove the button."""
    # Here we use `json.loads`, since the WebApp sends the data JSON serialized string
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    score = data.get('score')
    await update.message.reply_html(
        text=(
            f"You win today with {score} score!"
        ),
        reply_markup=ReplyKeyboardRemove(),
    )  
    # Обновляем рекорд в базе данных
    update_highscore(user.id, int(score))
 
# Основная функция запуска бота
def main():

    # Инициализация базы данных
    init_db()
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main() 
