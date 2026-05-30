from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime

app = FastAPI()

# CORS — разрешаем запросы из игры
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════
#  БАЗА ДАННЫХ
# ═══════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect("farm.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            full_name    TEXT,
            coins        REAL DEFAULT 0,
            clicks       INTEGER DEFAULT 0,
            level        INTEGER DEFAULT 1,
            referrer_id  INTEGER DEFAULT NULL,
            joined_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id  INTEGER,
            referred_id  INTEGER,
            coins_earned REAL DEFAULT 0,
            joined_at    TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()


def get_db():
    conn = sqlite3.connect("farm.db")
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════
#  МОДЕЛИ
# ═══════════════════════════════════════════════════════

class UserData(BaseModel):
    user_id:    int
    username:   str = ""
    full_name:  str = ""
    coins:      float = 0
    clicks:     int = 0
    level:      int = 1
    referrer_id: int = None


class SaveCoins(BaseModel):
    user_id: int
    coins:   float
    clicks:  int
    level:   int


# ═══════════════════════════════════════════════════════
#  API ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "CoinFarm API is running!"}


@app.post("/user/register")
def register_user(data: UserData):
    conn = get_db()
    c = conn.cursor()

    # Проверяем существует ли пользователь
    c.execute("SELECT * FROM users WHERE user_id = ?", (data.user_id,))
    existing = c.fetchone()

    if existing:
        conn.close()
        return {"status": "exists", "user": dict(existing)}

    # Создаём нового пользователя
    c.execute("""
        INSERT INTO users (user_id, username, full_name, coins, clicks, level, referrer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.user_id, data.username, data.full_name, 0, 0, 1, data.referrer_id))

    # Реферальный бонус
    if data.referrer_id:
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (data.referrer_id,))
        referrer = c.fetchone()
        if referrer:
            c.execute("UPDATE users SET coins = coins + 100 WHERE user_id = ?", (data.referrer_id,))
            c.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                      (data.referrer_id, data.user_id))

    conn.commit()
    conn.close()
    return {"status": "created"}


@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    c.execute("SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?", (user_id,))
    refs = c.fetchone()["count"]
    conn.close()

    result = dict(user)
    result["referrals"] = refs
    return result


@app.post("/user/save")
def save_progress(data: SaveCoins):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT coins FROM users WHERE user_id = ?", (data.user_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Реферальный бонус от новых монет
    earned = max(0, data.coins - existing["coins"])
    c.execute("SELECT referrer_id FROM users WHERE user_id = ?", (data.user_id,))
    ref = c.fetchone()
    if ref and ref["referrer_id"] and earned > 0:
        bonus = earned * 0.2  # 20%
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?",
                  (bonus, ref["referrer_id"]))
        c.execute("""UPDATE referrals SET coins_earned = coins_earned + ?
                     WHERE referrer_id = ? AND referred_id = ?""",
                  (bonus, ref["referrer_id"], data.user_id))

    c.execute("""UPDATE users SET coins = ?, clicks = ?, level = ?
                 WHERE user_id = ?""",
              (data.coins, data.clicks, data.level, data.user_id))
    conn.commit()
    conn.close()
    return {"status": "saved"}


@app.get("/top")
def get_top():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, full_name, coins, level FROM users ORDER BY coins DESC LIMIT 10")
    top = [dict(row) for row in c.fetchall()]
    conn.close()
    return top


@app.get("/referrals/{user_id}")
def get_referrals(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.full_name, u.coins, r.coins_earned, r.joined_at
        FROM referrals r
        JOIN users u ON u.user_id = r.referred_id
        WHERE r.referrer_id = ?
        ORDER BY r.joined_at DESC
    """, (user_id,))
    refs = [dict(row) for row in c.fetchall()]
    conn.close()
    return refs


