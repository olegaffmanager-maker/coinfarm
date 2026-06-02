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
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        keys INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        streak INTEGER DEFAULT 0,
        streak_day INTEGER DEFAULT 1,
        artifacts TEXT DEFAULT '{}',
        bosses TEXT DEFAULT '{}',
        rare_planets TEXT DEFAULT '{}',
        vip TEXT DEFAULT '{}',
        staked REAL DEFAULT 0,
        pvp_wins INTEGER DEFAULT 0,
        clan TEXT DEFAULT NULL,
        last_save INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        coins_earned REAL DEFAULT 0
    )""")
    # Add missing columns to existing DB (migration)
    new_columns = [
        ("keys", "INTEGER DEFAULT 0"),
        ("total_earned", "REAL DEFAULT 0"),
        ("streak", "INTEGER DEFAULT 0"),
        ("streak_day", "INTEGER DEFAULT 1"),
        ("artifacts", "TEXT DEFAULT '{}'"),
        ("bosses", "TEXT DEFAULT '{}'"),
        ("rare_planets", "TEXT DEFAULT '{}'"),
        ("vip", "TEXT DEFAULT '{}'"),
        ("staked", "REAL DEFAULT 0"),
        ("pvp_wins", "INTEGER DEFAULT 0"),
        ("clan", "TEXT DEFAULT NULL"),
        ("last_save", "INTEGER DEFAULT 0"),
    ]
    for col, coltype in new_columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {coltype}")
        except:
            pass  # Column already exists
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
        c.execute("UPDATE users SET coins=?, clicks=?, level=?, username=?, full_name=? WHERE user_id=?",
                  (max(coins, existing["coins"]), clicks, level, username, full_name, user_id))
        refs = get_referral_count(c, user_id)
        conn.commit()
        conn.close()
        return {"status": "exists", "referrals": refs, "coins": max(coins, existing["coins"])}

    c.execute("""INSERT INTO users (user_id, username, full_name, coins, clicks, level, referrer_id)
                 VALUES (?,?,?,?,?,?,?)""",
              (user_id, username, full_name, coins, clicks, level, referrer_id))

    if referrer_id and referrer_id != user_id:
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
        if c.fetchone():
            c.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (referrer_id,))
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
    if not user_id:
        return {"error": "no user_id"}
    try:
        user_id = int(user_id)
    except:
        return {"error": "invalid id"}

    coins        = request.get("coins", 0)
    clicks       = request.get("clicks", 0)
    level        = request.get("level", 1)
    keys         = request.get("keys", 0)
    total_earned = request.get("total_earned", 0)
    streak       = request.get("streak", 0)
    streak_day   = request.get("streak_day", 1)
    artifacts    = request.get("artifacts", "{}")
    bosses       = request.get("bosses", "{}")
    rare_planets = request.get("rare_planets", "{}")
    vip          = request.get("vip", "{}")
    staked       = request.get("staked", 0)
    pvp_wins     = request.get("pvp_wins", 0)
    clan         = request.get("clan", None)
    last_save    = request.get("last_save", 0)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT coins, referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return {"error": "not found"}

    # Referral passive income bonus
    earned = max(0, coins - row["coins"])
    if row["referrer_id"] and earned > 0:
        bonus = earned * 0.1
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (bonus, row["referrer_id"]))
        c.execute("UPDATE referrals SET coins_earned = coins_earned + ? WHERE referrer_id=? AND referred_id=?",
                  (bonus, row["referrer_id"], user_id))

    c.execute("""UPDATE users SET
        coins=?, clicks=?, level=?,
        keys=?, total_earned=?, streak=?, streak_day=?,
        artifacts=?, bosses=?, rare_planets=?,
        vip=?, staked=?, pvp_wins=?, clan=?, last_save=?
        WHERE user_id=?""",
        (coins, clicks, level,
         keys, total_earned, streak, streak_day,
         artifacts, bosses, rare_planets,
         vip, staked, pvp_wins, clan, last_save,
         user_id))
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

# ═══ PROMO CODE ACTIVATION (from bot) ═══
PROMO_CODES = {
    'XSPACE2026':  {'reward': 'coins', 'value': 10000},
    'LAUNCH':      {'reward': 'coins', 'value': 25000},
    'XKEY2026':    {'reward': 'keys',  'value': 3},
    'SPACE100':    {'reward': 'coins', 'value': 5000},
    'WELCOMEGIFT': {'reward': 'both',  'value': 5000,  'value2': 1},
    'XSPC_TG':     {'reward': 'both',  'value': 8000,  'value2': 1},
    'GALAXY2026':  {'reward': 'coins', 'value': 15000},
    'MINEHARD':    {'reward': 'coins', 'value': 7500},
    'PLANET5':     {'reward': 'both',  'value': 10000, 'value2': 2},
    'XSPACE_VIP':  {'reward': 'both',  'value': 20000, 'value2': 3},
    'CRYPTO100':   {'reward': 'coins', 'value': 12000},
    'TONCHAIN':    {'reward': 'both',  'value': 6000,  'value2': 1},
    'SUMMER2026':  {'reward': 'coins', 'value': 30000},
    'ASTEROID':    {'reward': 'both',  'value': 5000,  'value2': 2},
}

@app.post("/promo/redeem")
async def redeem_promo(request: dict):
    user_id = request.get("user_id")
    code    = str(request.get("code", "")).strip().upper()

    if not user_id or not code:
        return {"error": "missing fields"}
    try:
        user_id = int(user_id)
    except:
        return {"error": "invalid user_id"}

    promo = PROMO_CODES.get(code)
    if not promo:
        return {"error": "invalid_code", "msg": "❌ Invalid promo code"}

    conn = get_db()
    c = conn.cursor()

    # Check if already used
    c.execute("SELECT user_id FROM promo_used WHERE user_id=? AND code=?", (user_id, code))

    # Create table if not exists
    c.execute("""CREATE TABLE IF NOT EXISTS promo_used (
        user_id INTEGER, code TEXT, used_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, code)
    )""")

    c.execute("SELECT 1 FROM promo_used WHERE user_id=? AND code=?", (user_id, code))
    if c.fetchone():
        conn.close()
        return {"error": "already_used", "msg": "⚠️ Code already used"}

    # Apply reward
    coins_reward = 0
    keys_reward  = 0

    if promo['reward'] == 'coins':
        coins_reward = promo['value']
    elif promo['reward'] == 'keys':
        keys_reward = promo['value']
    elif promo['reward'] == 'both':
        coins_reward = promo['value']
        keys_reward  = promo.get('value2', 0)

    c.execute("UPDATE users SET coins = coins + ?, keys = keys + ? WHERE user_id = ?",
              (coins_reward, keys_reward, user_id))
    c.execute("INSERT INTO promo_used (user_id, code) VALUES (?, ?)", (user_id, code))
    conn.commit()
    conn.close()

    msg = f"✅ Code activated!"
    if coins_reward: msg += f"\n+{coins_reward:,} XSPC"
    if keys_reward:  msg += f"\n+{keys_reward} XKEY 🔑"

    return {"status": "ok", "msg": msg, "coins": coins_reward, "keys": keys_reward}

# ═══ PUSH NOTIFICATIONS ═══
# Store pending energy notifications
energy_notify_users = set()

@app.post("/notify/energy")
async def notify_energy(request: dict):
    """Called by game when player's energy is full"""
    user_id = request.get("user_id")
    if not user_id:
        return {"error": "no user_id"}
    # Store for bot to pick up
    energy_notify_users.add(int(user_id))
    return {"status": "queued"}

@app.get("/notify/pending")
def get_pending_notifications():
    """Bot polls this to get users who need energy notification"""
    users = list(energy_notify_users)
    energy_notify_users.clear()
    return {"users": users}

# ═══ STARS PAYMENT INVOICES ═══
@app.get("/invoice/{package_type}")
def create_invoice(package_type: str):
    PACKAGES = {
        'booster':     {'title': '⚡ Booster Pack',  'description': 'x1.5 all bonuses for 7 days + 5 XKEY', 'amount': 50},
        'vip_month':   {'title': '👑 VIP Month',     'description': 'x2 all bonuses for 30 days + 20 XKEY', 'amount': 200},
        'galaxy_pass': {'title': '🌌 Galaxy Pass',   'description': 'Permanent x2 bonus + 100 XKEY',        'amount': 1000},
        'xspc_pack':   {'title': '🪐 XSPC Pack',     'description': '+50,000 XSPC instantly',               'amount': 30},
        'key_pack':    {'title': '🔑 Key Pack',      'description': '+10 XKEY instantly',                   'amount': 25},
        'energy_pack': {'title': '⚡ Energy Pack',   'description': 'Unlimited energy for 24 hours',        'amount': 15},
    }
    pkg = PACKAGES.get(package_type)
    if not pkg:
        return {"error": "unknown package"}
    return {"title": pkg['title'], "description": pkg['description'],
            "currency": "XTR", "amount": pkg['amount'], "payload": package_type}
