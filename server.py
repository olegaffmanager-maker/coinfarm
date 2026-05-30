from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    conn = sqlite3.connect("farm.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '',
        full_name TEXT DEFAULT '', coins REAL DEFAULT 0,
        clicks INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
        referrer_id INTEGER DEFAULT NULL, joined_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER, referred_id INTEGER, coins_earned REAL DEFAULT 0)""")
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def root():
    return {"status": "CoinFarm API is running!"}

@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return {"error": "not found"}
    c.execute("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = ?", (user_id,))
    refs = c.fetchone()["cnt"]
    conn.close()
    result = dict(user)
    result["referrals"] = refs
    return result

@app.post("/user/register")
async def register_user(request: dict):
    user_id = request.get("user_id")
    username = request.get("username", "")
    full_name = request.get("full_name", "")
    referrer_id = request.get("referrer_id")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone():
        conn.close()
        return {"status": "exists"}
    c.execute("INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?,?,?,?)",
              (user_id, username, full_name, referrer_id))
    if referrer_id:
        c.execute("UPDATE users SET coins = coins + 100 WHERE user_id = ?", (referrer_id,))
        c.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?,?)", (referrer_id, user_id))
    conn.commit()
    conn.close()
    return {"status": "created"}

@app.post("/user/save")
async def save_progress(request: dict):
    user_id = request.get("user_id")
    coins = request.get("coins", 0)
    clicks = request.get("clicks", 0)
    level = request.get("level", 1)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT coins, referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"error": "not found"}
    earned = max(0, coins - row["coins"])
    if row["referrer_id"] and earned > 0:
        bonus = earned * 0.2
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (bonus, row["referrer_id"]))
    c.execute("UPDATE users SET coins=?, clicks=?, level=? WHERE user_id=?", (coins, clicks, level, user_id))
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

@app.get("/user/{user_id}/friends")
def get_friends(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT u.user_id, u.full_name, u.coins, u.level
        FROM referrals r JOIN users u ON u.user_id = r.referred_id
        WHERE r.referrer_id = ? ORDER BY u.coins DESC""", (user_id,))
    friends = [dict(row) for row in c.fetchall()]
    conn.close()
    return friends
