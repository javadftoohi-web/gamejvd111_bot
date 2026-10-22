import os
import sqlite3

DB_PATH = os.getenv("DATABASE_PATH", "gamehub.sqlite3")

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT NOT NULL DEFAULT '',
            points INTEGER NOT NULL DEFAULT 0, wins INTEGER NOT NULL DEFAULT 0,
            games INTEGER NOT NULL DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS group_quiz_votes (
            chat_id INTEGER NOT NULL, quiz_id TEXT NOT NULL, user_id INTEGER NOT NULL,
            choice INTEGER NOT NULL, correct INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(chat_id, quiz_id, user_id)
        )""")

def upsert(user):
    with connect() as c:
        c.execute("""INSERT INTO players(user_id, username, first_name) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name""",
            (user.id, user.username, user.first_name or ""))

def add_result(user, points, won=False):
    upsert(user)
    with connect() as c:
        c.execute("UPDATE players SET points=MAX(0, points+?), games=games+1, wins=wins+? WHERE user_id=?",
                  (points, 1 if won else 0, user.id))

def get_profile(user):
    upsert(user)
    with connect() as c:
        r = c.execute("SELECT * FROM players WHERE user_id=?", (user.id,)).fetchone()
        return dict(r)

def leaderboard(limit=10):
    with connect() as c:
        rows = c.execute("SELECT * FROM players ORDER BY points DESC, wins DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
