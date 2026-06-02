from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# PostgreSQL через psycopg2
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Если есть PostgreSQL — используем его, иначе SQLite
if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_PG = True
    logging.info("Using PostgreSQL")
else:
    import sqlite3
    USE_PG = False
    logging.info("Using SQLite (temporary)")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect("farm.db")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    if USE_PG:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT DEFAULT '',
            full_name TEXT DEFAULT '',
            coins FLOAT DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            referrer_id BIGINT DEFAULT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keys INTEGER DEFAULT 0,
            total_earned FLOAT DEFAULT 0,
            streak INTEGER DEFAULT 0,
            streak_day INTEGER DEFAULT 1,
            artifacts TEXT DEFAULT '{}',
            bosses TEXT DEFAULT '{}',
            rare_planets TEXT DEFAULT '{}',
            vip TEXT DEFAULT '{}',
            staked FLOAT DEFAULT 0,
            pvp_wins INTEGER DEFAULT 0,
            clan TEXT DEFAULT NULL,
            last_save BIGINT DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS referrals (
            referrer_id BIGINT,
            referred_id BIGINT,
            coins_earned FLOAT DEFAULT 0,
            PRIMARY KEY (referrer_id, referred_id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS promo_used (
            user_id BIGINT,
            code TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, code)
        )""")
    else:
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
        c.execute("""CREATE TABLE IF NOT EXISTS promo_used (
            user_id INTEGER,
            code TEXT,
            used_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, code)
        )""")
        # Auto-migrate
        new_cols = [
            ("keys","INTEGER DEFAULT 0"),("total_earned","REAL DEFAULT 0"),
            ("streak","INTEGER DEFAULT 0"),("streak_day","INTEGER DEFAULT 1"),
            ("artifacts","TEXT DEFAULT '{}'"),("bosses","TEXT DEFAULT '{}'"),
            ("rare_planets","TEXT DEFAULT '{}'"),("vip","TEXT DEFAULT '{}'"),
            ("staked","REAL DEFAULT 0"),("pvp_wins","INTEGER DEFAULT 0"),
            ("clan","TEXT DEFAULT NULL"),("last_save","INTEGER DEFAULT 0"),
        ]
        for col, ct in new_cols:
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {ct}")
            except: pass
    conn.commit()
    conn.close()

init_db()

def get_referral_count(c, user_id):
    if USE_PG:
        c.execute("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = %s", (user_id,))
    else:
        c.execute("SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = ?", (user_id,))
    row = c.fetchone()
    return row['cnt'] if row else 0

def q(sql):
    """Convert ? placeholders to %s for PostgreSQL"""
    if USE_PG:
        return sql.replace('?', '%s')
    return sql

@app.get("/")
def root():
    return {"status": "XSPACECOIN API running 🪐", "db": "postgresql" if USE_PG else "sqlite"}

@app.get("/stats")
def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM users")
    total = c.fetchone()['total'] or 0
    c.execute("SELECT SUM(coins) as total_coins FROM users")
    total_coins = c.fetchone()['total_coins'] or 0
    conn.close()
    return {"total_players": total, "total_coins": int(total_coins)}

@app.get("/top")
def get_top():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, full_name, coins, level FROM users ORDER BY coins DESC LIMIT 50")
    top = [dict(row) for row in c.fetchall()]
    conn.close()
    return top

@app.get("/user/{user_id}")
def get_user(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute(q("SELECT * FROM users WHERE user_id = ?"), (user_id,))
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
    c.execute(q("""
        SELECT u.user_id, u.full_name, u.username, u.coins, u.level, r.coins_earned
        FROM referrals r
        JOIN users u ON u.user_id = r.referred_id
        WHERE r.referrer_id = ?
        ORDER BY u.coins DESC
    """), (user_id,))
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
    c.execute(q("SELECT user_id, coins FROM users WHERE user_id = ?"), (user_id,))
    existing = c.fetchone()

    if existing:
        existing_coins = existing['coins']
        c.execute(q("UPDATE users SET coins=?, clicks=?, level=?, username=?, full_name=? WHERE user_id=?"),
                  (max(coins, existing_coins), clicks, level, username, full_name, user_id))
        # Add referral if provided and not yet linked
        if referrer_id and referrer_id != user_id:
            c.execute(q("SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?"), (referrer_id, user_id))
            if not c.fetchone():
                c.execute(q("INSERT INTO referrals (referrer_id, referred_id) VALUES (?,?)"), (referrer_id, user_id))
                c.execute(q("SELECT user_id FROM users WHERE user_id=?"), (referrer_id,))
                if c.fetchone():
                    c.execute(q("UPDATE users SET coins=coins+5000 WHERE user_id=?"), (referrer_id,))
        refs = get_referral_count(c, user_id)
        conn.commit()
        conn.close()
        return {"status": "exists", "referrals": refs, "coins": max(coins, existing_coins)}

    # New user
    c.execute(q("INSERT INTO users (user_id, username, full_name, coins, clicks, level, referrer_id) VALUES (?,?,?,?,?,?,?)"),
              (user_id, username, full_name, coins, clicks, level, referrer_id))

    if referrer_id and referrer_id != user_id:
        c.execute(q("SELECT 1 FROM referrals WHERE referrer_id=? AND referred_id=?"), (referrer_id, user_id))
        if not c.fetchone():
            c.execute(q("INSERT INTO referrals (referrer_id, referred_id) VALUES (?,?)"), (referrer_id, user_id))
        c.execute(q("SELECT user_id FROM users WHERE user_id=?"), (referrer_id,))
        if c.fetchone():
            c.execute(q("UPDATE users SET coins=coins+5000 WHERE user_id=?"), (referrer_id,))
            logging.info(f"Referral: {referrer_id} invited {user_id}, +5000 XSPC")

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
    c.execute(q("SELECT coins, referrer_id FROM users WHERE user_id = ?"), (user_id,))
    row = c.fetchone()

    if not row:
        # Auto-register if not exists
        c.execute(q("INSERT INTO users (user_id, coins, clicks, level, keys, total_earned, streak, last_save) VALUES (?,?,?,?,?,?,?,?)"),
                  (user_id, coins, clicks, level, keys, total_earned, streak, last_save))
        conn.commit()
        conn.close()
        return {"status": "created"}

    # Referral passive bonus
    old_coins = row['coins']
    earned = max(0, coins - old_coins)
    referrer_id = row['referrer_id']
    if referrer_id and earned > 0:
        bonus = earned * 0.05
        c.execute(q("UPDATE users SET coins=coins+? WHERE user_id=?"), (bonus, referrer_id))

    c.execute(q("""UPDATE users SET
        coins=?, clicks=?, level=?,
        keys=?, total_earned=?, streak=?, streak_day=?,
        artifacts=?, bosses=?, rare_planets=?,
        vip=?, staked=?, pvp_wins=?, clan=?, last_save=?
        WHERE user_id=?"""),
        (coins, clicks, level, keys, total_earned, streak, streak_day,
         artifacts, bosses, rare_planets, vip, staked, pvp_wins, clan, last_save,
         user_id))
    conn.commit()

    refs = get_referral_count(c, user_id)
    conn.close()
    return {"status": "saved", "referrals": refs}

# ═══ PROMO CODES ═══
PROMO_CODES = {
    'XSPACE2026':  {'coins': 10000, 'keys': 0},
    'LAUNCH':      {'coins': 25000, 'keys': 0},
    'XKEY2026':    {'coins': 0,     'keys': 3},
    'SPACE100':    {'coins': 5000,  'keys': 0},
    'WELCOMEGIFT': {'coins': 5000,  'keys': 1},
    'XSPC_TG':     {'coins': 8000,  'keys': 1},
    'GALAXY2026':  {'coins': 15000, 'keys': 0},
    'MINEHARD':    {'coins': 7500,  'keys': 0},
    'PLANET5':     {'coins': 10000, 'keys': 2},
    'XSPACE_VIP':  {'coins': 20000, 'keys': 3},
    'CRYPTO100':   {'coins': 12000, 'keys': 0},
    'TONCHAIN':    {'coins': 6000,  'keys': 1},
    'SUMMER2026':  {'coins': 30000, 'keys': 0},
    'ASTEROID':    {'coins': 5000,  'keys': 2},
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
    c.execute(q("SELECT 1 FROM promo_used WHERE user_id=? AND code=?"), (user_id, code))
    if c.fetchone():
        conn.close()
        return {"error": "already_used", "msg": "⚠️ Code already used"}

    coins_r = promo['coins']
    keys_r  = promo['keys']
    c.execute(q("UPDATE users SET coins=coins+?, keys=keys+? WHERE user_id=?"), (coins_r, keys_r, user_id))
    c.execute(q("INSERT INTO promo_used (user_id, code) VALUES (?,?)"), (user_id, code))
    conn.commit()
    conn.close()

    msg = "✅ Code activated!"
    if coins_r: msg += f"\n+{coins_r:,} XSPC"
    if keys_r:  msg += f"\n+{keys_r} XKEY 🔑"
    return {"status": "ok", "msg": msg, "coins": coins_r, "keys": keys_r}

# ═══ NOTIFY ═══
energy_notify_users = set()

@app.post("/notify/energy")
async def notify_energy(request: dict):
    user_id = request.get("user_id")
    if user_id:
        energy_notify_users.add(int(user_id))
    return {"status": "queued"}

@app.get("/notify/pending")
def get_pending():
    users = list(energy_notify_users)
    energy_notify_users.clear()
    return {"users": users}

# ═══ DEBUG ═══
@app.get("/debug/referrals/{user_id}")
def debug_referrals(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute(q("SELECT * FROM referrals WHERE referrer_id=?"), (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    count = get_referral_count(c, user_id)
    conn.close()
    return {"referrer_id": user_id, "count": count, "referrals": rows}

# ═══ INVOICES ═══
@app.get("/invoice/{package_type}")
def create_invoice(package_type: str):
    PACKAGES = {
        'booster':     {'title': '⚡ Booster Pack',  'description': 'x1.5 all bonuses 7 days', 'amount': 50},
        'vip_month':   {'title': '👑 VIP Month',     'description': 'x2 all bonuses 30 days',  'amount': 200},
        'galaxy_pass': {'title': '🌌 Galaxy Pass',   'description': 'Permanent x2 bonus',      'amount': 1000},
        'xspc_pack':   {'title': '🪐 XSPC Pack',     'description': '+50,000 XSPC',             'amount': 30},
        'key_pack':    {'title': '🔑 Key Pack',      'description': '+10 XKEY',                  'amount': 25},
        'energy_pack': {'title': '⚡ Energy Pack',   'description': 'Unlimited energy 24h',     'amount': 15},
    }
    pkg = PACKAGES.get(package_type)
    if not pkg:
        return {"error": "unknown package"}
    return {"title": pkg['title'], "description": pkg['description'],
            "currency": "XTR", "amount": pkg['amount'], "payload": package_type}
