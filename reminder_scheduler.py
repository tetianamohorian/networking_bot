import sqlite3
import threading
import time
from datetime import datetime, timedelta
from request_manager import DB_PATH
from telebot import TeleBot
from db import get_user_language
from translator import Translator

REMINDER_HOURS_BEFORE = 3  

def start_reminder_loop(bot: TeleBot, translator: Translator):
    def loop():
        while True:
            check_and_send_reminders(bot, translator)
            time.sleep(60)  # Проверка каждую минуту
    threading.Thread(target=loop, daemon=True).start()

def check_and_send_reminders(bot: TeleBot, translator: Translator):
    now = datetime.now()
    print(f"🕒 Сейчас {now.strftime('%d.%m.%Y %H:%M:%S')}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, taken_by, taken_by_id, deadline, reminded 
        FROM requests 
        WHERE reminded = 0 AND taken_by IS NOT NULL AND taken_by_id IS NOT NULL
    """)
    rows = cursor.fetchall()

    for req_id, taken_by, taken_by_id, deadline_str, reminded in rows:
        print(f"🕓 Проверяю заявку #{req_id} с дедлайном {deadline_str}")
        if not deadline_str or deadline_str.strip() == "-":
            continue

        try:
            deadline = parse_deadline(deadline_str)
        except Exception as e:
            print(f"⚠️ Невозможно распарсить дедлайн заявки #{req_id}: {e}")
            continue

        time_before_deadline = (deadline - now).total_seconds() / 60  
        if 0 <= time_before_deadline <= REMINDER_HOURS_BEFORE * 60:
            executor_id = taken_by_id
            hours = int(time_before_deadline // 60)
            minutes = int(time_before_deadline % 60)

            print(f"📬 Отправляю напоминание исполнителю {executor_id} (взял: {taken_by}) по заявке #{req_id} (осталось {hours}ч {minutes}м)")
            lang = get_user_language(executor_id)
            msg = translator.t("reminder_text", lang).format(req_id=req_id, hours=hours, minutes=minutes)

            try:
                bot.send_message(executor_id, msg)
            except Exception as e:
                print(f"⚠️ Ошибка при отправке напоминания #{req_id} исполнителю {executor_id}: {e}")
            else:
                cursor.execute("UPDATE requests SET reminded = 1 WHERE id = ?", (req_id,))
                conn.commit()
        else:
            print(f"⏳ НЕ отправлено: заявка #{req_id}, осталось {time_before_deadline:.1f} мин (напоминаем за {REMINDER_HOURS_BEFORE * 60:.0f} мин)")

    conn.close()

def parse_deadline(deadline_str):
    try:
        return datetime.strptime(deadline_str.strip(), "%d.%m.%Y %H:%M")
    except Exception as e:
        print(f"❌ Ошибка парсинга дедлайна '{deadline_str}': {e}")
        raise
