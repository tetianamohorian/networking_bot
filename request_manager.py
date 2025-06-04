import sqlite3

DB_PATH = "data/requests.db"
TEAM_CHAT_ID = -4804986028
from telebot import types
from db import get_user_language


def init_request_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER,
            requester_username TEXT,
            subject TEXT,
            action TEXT,
            deadline TEXT,
            details TEXT,
            message_id INTEGER,
            status TEXT DEFAULT 'open',
            taken_by TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN reminded INTEGER DEFAULT 0;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN taken_by_id INTEGER;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

    try:
        cursor.execute("ALTER TABLE requests ADD COLUMN rating INTEGER;")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

    conn.commit()
    conn.close()


def save_request(user_id, username, subject, action, deadline, details, message_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO requests (
            requester_id,
            requester_username,
            subject,
            action,
            deadline,
            details,
            message_id,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, subject, action, deadline, details, message_id, "open"))

    conn.commit()
    req_id = cursor.lastrowid
    conn.close()
    return req_id

def format_request_card(req_id, username, subject, action_key, deadline, details, translator, lang):
    action = translator.t(action_key, lang)
    return f"""
📩 <b>{translator.t("new_request", lang)} #{req_id}</b>
👤 <b>{translator.t("from", lang)}</b> @{username}
📘 <b>{translator.t("subject", lang)}</b> {subject.replace('_', ' ')}
🧾 <b>{translator.t("type", lang)}</b> {action}
📅 <b>{translator.t("deadline", lang)}</b> {deadline}
📝 <b>{translator.t("details", lang)}</b> {details}
"""


def mark_request_as_taken(req_id, user):
    import sqlite3
    from request_manager import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверка: есть ли открытая заявка
    cursor.execute("SELECT requester_id, message_id FROM requests WHERE id = ? AND status = 'open'", (req_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False, None, None, None

    requester_id, message_id = result

    # Сохраняем: имя или ID для отображения, и ID для надёжной отправки
    taken_by_display = user.username or f"ID {user.id}"
    taken_by_id = user.id

    cursor.execute("""
        UPDATE requests
        SET status = ?, taken_by = ?, taken_by_id = ?
        WHERE id = ?
    """, ("taken", taken_by_display, taken_by_id, req_id))

    conn.commit()
    conn.close()

    return True, requester_id, message_id, TEAM_CHAT_ID


def get_request(req_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 👈 доступ по имени
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def mark_request_as_done(request_id, bot, translator):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Обновляем статус заявки
    cursor.execute("UPDATE requests SET status = ? WHERE id = ?", ("done", request_id))
    conn.commit()

    # Получаем ID заказчика и исполнителя
    cursor.execute("SELECT requester_id, taken_by_id FROM requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"⚠️ Заявка #{request_id} не найдена для оценки.")
        return

    requester_id, executor_id = row

    # Определяем язык заказчика
    lang = get_user_language(requester_id)

    # Создаём кнопки для оценки от 1 до 5
    markup = types.InlineKeyboardMarkup()
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate|{request_id}|{i}"))

    # Перевод сообщения
    rating_prompt = translator.t("rate_prompt", lang)

    # Отправляем заказчику сообщение
    bot.send_message(requester_id, rating_prompt, reply_markup=markup)


def get_requests_by_user(user_id, status=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM requests WHERE requester_id = ? AND status = ?", (user_id, status))
    else:
        cursor.execute("SELECT * FROM requests WHERE requester_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows



def get_requests_taken_by_user(user, status=None):
    user_id = str(user.id)
    username = user.username
    id_fallback = f"ID {user.id}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if username:
        query = """
        SELECT * FROM requests WHERE 
        (taken_by = ? OR taken_by = ? OR taken_by = ?)
        """
        params = (user_id, id_fallback, username)
    else:
        query = """
        SELECT * FROM requests WHERE 
        (taken_by = ? OR taken_by = ?)
        """
        params = (user_id, id_fallback)

    if status:
        query += " AND status = ?"
        params += (status,)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows




def get_user_request_if_editable(user_id, request_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM requests WHERE id = ? AND requester_id = ? AND status = 'open'",
        (request_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def update_request_field(request_id, field, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE requests SET {field} = ? WHERE id = ?", (value, request_id))
    conn.commit()
    conn.close()


def delete_user_request_if_allowed(request_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT status, message_id FROM requests WHERE id = ? AND requester_id = ?", (request_id, user_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, None  # возвращаем 2 значения

    status, message_id = row
    if status != "open":
        conn.close()
        return False, None

    cursor.execute("DELETE FROM requests WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    return True, message_id  # <== нужно вернуть message_id

