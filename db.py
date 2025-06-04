import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.db")

def get_db():
    return sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)

def init_db():
    with get_db() as conn:
        with open("migrations/init.sql", encoding="utf-8") as f:
            conn.executescript(f.read())

def set_user_language(telegram_id, lang):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, language)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET language=excluded.language;
        """, (telegram_id, lang))

def get_user_language(telegram_id):
    with get_db() as conn:
        row = conn.execute("SELECT language FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        return row[0] if row else "sk"