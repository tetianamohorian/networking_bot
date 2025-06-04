import os
import telebot
from db import init_db, get_user_language
from translator import Translator
from request_manager import init_request_db
from handlers import start, course, subject_router, request_form, executor_handler
from reminder_scheduler import start_reminder_loop
import sqlite3

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7952204712:AAEBP8vaZBP6hDoD7HkxlEKPWD6xKIkRU94"
bot = telebot.TeleBot(BOT_TOKEN)
DB_PATH = "data/requests.db"
translator = Translator()

# Register handlers
start.register(bot, translator)
course.register(bot, translator)
subject_router.register(bot, translator)
request_form.register(bot, translator)
executor_handler.register(bot, translator)
start_reminder_loop(bot, translator)



@bot.callback_query_handler(func=lambda call: call.data.startswith("rate|"))
def handle_rating(call):
    _, req_id, rating = call.data.split("|")
    req_id = int(req_id)
    rating = int(rating)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET rating = ? WHERE id = ?", (rating, req_id))
    cursor.execute("SELECT taken_by_id FROM requests WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    lang = get_user_language(call.from_user.id)
    bot.answer_callback_query(call.id, translator.t("thank_you_rating", lang))


    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


    if row and row[0]:
        executor_id = row[0]
        try:
            bot.send_message(executor_id, translator.t("you_were_rated", lang).format(rating=rating, req_id=req_id))
        except Exception as e:
            print(f"⚠️ Не удалось отправить оценку исполнителю: {e}")


if __name__ == '__main__':
    print("✅ Bot is starting...")
    init_db()
    init_request_db()
    bot.polling()
