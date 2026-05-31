from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect("farm.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT DEFAULT '',
        full_name TEXT DEFAULT '',
        coins REAL DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        referrer_id INTEGER DEFAULT NULL,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        coins_earned REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

def get_referral_count(c, user_id):
    c.execute("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = ?", (user_id,))
    return c.fetchone()["cnt"]

@app.get("/")
def root():
    return {"status": "XSPACECOIN API is running! 🪐"}

@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return {"error": "not found"}
    refs = get_referral_count(c, user_id)
    conn.close()
    result = dict(user)
    result["referrals"] = refs
    return result

@app.get("/user/{user_id}/friends")
def get_friends(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.user_id, u.full_name, u.coins, u.level
        FROM referrals r
        JOIN users u ON u.user_id = r.referred_id
        WHERE r.referrer_id = ?
        ORDER BY u.coins DESC
    """, (user_id,))
    friends = [dict(row) for row in c.fetchall()]
    refs = get_referral_count(c, user_id)
    conn.close()
    return {"friends": friends, "referrals": refs}

@app.post("/user/register")
async def register_user(request: dict):
    user_id = request.get("telegram_id") or request.get("user_id")
    username = request.get("username", "")
    full_name = request.get("full_name", "")
    # Accept both ref_id and referrer_id
    referrer_id = request.get("ref_id") or request.get("referrer_id")
    coins = request.get("coins", 0)
    level = request.get("level", 1)
    clicks = request.get("clicks", 0)

    if not user_id:
        return {"error": "no user_id"}

    try:
        user_id = int(user_id)
        referrer_id = int(referrer_id) if referrer_id else None
    except:
        return {"error": "invalid id"}

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT user_id, coins FROM users WHERE user_id = ?", (user_id,))
    existing = c.fetchone()

    if existing:
        # User exists — update and return referral count
        c.execute("UPDATE users SET coins=?, clicks=?, level=?, username=?, full_name=? WHERE user_id=?",
                  (max(coins, existing["coins"]), clicks, level, username, full_name, user_id))
        refs = get_referral_count(c, user_id)
        conn.commit()
        conn.close()
        return {"status": "exists", "referrals": refs, "coins": max(coins, existing["coins"])}

    # New user
    c.execute("INSERT INTO users (user_id, username, full_name, coins, clicks, level, referrer_id) VALUES (?,?,?,?,?,?,?)",
              (user_id, username, full_name, coins, clicks, level, referrer_id))

    if referrer_id and referrer_id != user_id:
        # Check referrer exists
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
        if c.fetchone():
            # Give referrer bonus
            c.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (referrer_id,))
            # Check not already referred
            c.execute("SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?", (referrer_id, user_id))
            if not c.fetchone():
                c.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?,?)",
                          (referrer_id, user_id))

    conn.commit()

    refs = get_referral_count(c, user_id)
    conn.close()
    return {"status": "created", "referrals": refs}

@app.post("/user/save")
async def save_progress(request: dict):
    user_id = request.get("telegram_id") or request.get("user_id")
    coins = request.get("coins", 0)
    clicks = request.get("clicks", 0)
    level = request.get("level", 1)

    if not user_id:
        return {"error": "no user_id"}

    try:
        user_id = int(user_id)
    except:
        return {"error": "invalid id"}

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT coins, referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return {"error": "not found"}

    earned = max(0, coins - row["coins"])
    if row["referrer_id"] and earned > 0:
        bonus = earned * 0.1
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (bonus, row["referrer_id"]))
        c.execute("UPDATE referrals SET coins_earned = coins_earned + ? WHERE referrer_id=? AND referred_id=?",
                  (bonus, row["referrer_id"], user_id))

    c.execute("UPDATE users SET coins=?, clicks=?, level=? WHERE user_id=?",
              (coins, clicks, level, user_id))
    conn.commit()

    refs = get_referral_count(c, user_id)
    conn.close()
    return {"status": "saved", "referrals": refs}

@app.get("/top")
def get_top():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, full_name, coins, level FROM users ORDER BY coins DESC LIMIT 50")
    top = [dict(row) for row in c.fetchall()]
    conn.close()
    return top

@app.get("/stats")
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM users")
    total = c.fetchone()["total"]
    c.execute("SELECT SUM(coins) as total_coins FROM users")
    total_coins = c.fetchone()["total_coins"] or 0
    conn.close()
    return {"total_players": total, "total_coins": int(total_coins)}
