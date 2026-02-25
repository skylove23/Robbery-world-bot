import os
import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from collections import defaultdict

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8364698101:AAGuNoR0Qhf2QwAxP5xjw9tgmHMtE3VE6tg"
OWNER_ID = 5092771309
OWNER_USERNAME = "@Skynotur12"
BOT_NAME = "Robbery World"

# Create users.txt if not exists
if not os.path.exists('users.txt'):
    with open('users.txt', 'w') as f:
        f.write('{}')

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.data_file = 'users.txt'
        self.load_data()
    
    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                self.users = json.load(f)
        except:
            self.users = {}
            self.save_data()
    
    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def get_user(self, user_id, username=None, first_name=None):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                'username': username,
                'name': first_name or username or f"User{user_id[:5]}",
                'balance': 400,  # Starting balance $400
                'status': 'alive',
                'premium': False,
                'premium_expiry': None,
                'rank': '🥚 Egg',
                'protection': {
                    'active': False,
                    'expiry': None,
                    'days': 0
                },
                'last_attacked': None,
                'death_time': None,
                'total_earned': 400,
                'total_lost': 0,
                'rob_count': 0,
                'kill_count': 0,
                'death_count': 0,
                'revive_count': 0,
                'gifts_received': [],
                'gifts_given': [],
                'daily_streak': 0,
                'last_daily': None,
                'last_mega_rob': None,
                'last_mega_kill': None,
                'last_godmode': None,
                'joined_date': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'language': 'en'
            }
            self.save_data()
        return self.users[user_id]
    
    def update_user(self, user_id, data):
        user_id = str(user_id)
        if user_id in self.users:
            self.users[user_id].update(data)
        self.users[user_id]['last_active'] = datetime.now().isoformat()
        self.save_data()
    
    def get_all_users(self):
        return self.users
    
    def get_leaderboard(self, limit=100):
        users = []
        for uid, data in self.users.items():
            if data['status'] == 'alive' or (data['status'] == 'dead' and data.get('death_time')):
                users.append({
                    'id': uid,
                    'name': data['name'],
                    'balance': data['balance'],
                    'status': data['status'],
                    'premium': data.get('premium', False)
                })
        return sorted(users, key=lambda x: x['balance'], reverse=True)[:limit]

db = Database()

# ==================== GIFTS (30 Under $10000) ====================
GIFTS = {
    '🌹 Rose': 100,
    '🍫 Chocolate': 200,
    '🧸 Teddy Bear': 300,
    '👃 Perfume': 400,
    '⌚ Watch': 500,
    '📿 Necklace': 600,
    '💍 Ring': 700,
    '📿 Bracelet': 800,
    '🕶️ Sunglasses': 900,
    '👛 Wallet': 1000,
    '🎀 Belt': 1100,
    '🧢 Hat': 1200,
    '👟 Shoes': 1300,
    '🧥 Jacket': 1400,
    '👖 Jeans': 1500,
    '👕 Shirt': 1600,
    '👗 Dress': 1700,
    '🎒 Bag': 1800,
    '🎒 Backpack': 1900,
    '🎧 Headphones': 2000,
    '🔊 Speaker': 2500,
    '📷 Camera': 3000,
    '⌚ Smartwatch': 3500,
    '📱 Tablet': 4000,
    '📱 Smartphone': 5000,
    '💻 Laptop': 6000,
    '🚲 Bicycle': 7000,
    '🛵 Scooter': 8000,
    '🏍️ Bike': 9000,
    '🚗 Car': 10000,
}

# ==================== RANK BADGES ====================
RANK_BADGES = {
    '🥚 Egg': {'emoji': '🥚', 'name': 'Egg'},
    '🐣 Chick': {'emoji': '🐣', 'name': 'Chick'},
    '🐦 Bird': {'emoji': '🐦', 'name': 'Bird'},
    '🦅 Eagle': {'emoji': '🦅', 'name': 'Eagle'},
    '🦁 Lion': {'emoji': '🦁', 'name': 'Lion'},
    '🐉 Dragon': {'emoji': '🐉', 'name': 'Dragon'},
    '👑 King': {'emoji': '👑', 'name': 'King'},
    '⚡ Emperor': {'emoji': '⚡', 'name': 'Emperor'},
    '🌟 Legend': {'emoji': '🌟', 'name': 'Legend'},
    '🕊️ Mythic': {'emoji': '🕊️', 'name': 'Mythic'},
    '🔥 Immortal': {'emoji': '🔥', 'name': 'Immortal'},
    '💫 God': {'emoji': '💫', 'name': 'God'},
}

# ==================== TOP 20 BADGES ====================
TOP_20_BADGES = {
    1: '👑🔥 KING OF KINGS',
    2: '⚡👑 THUNDER LORD',
    3: '🌟👑 STAR EMPEROR',
    4: '💎👑 DIAMOND HANDS',
    5: '🦅👑 WRAITH LORD',
    6: '🐉👑 DRAGON SLAYER',
    7: '🦁👑 LIONHEART',
    8: '⚡👑 THOR\'S HAMMER',
    9: '🗡️👑 BLADE MASTER',
    10: '🛡️👑 IRON WALL',
    11: '⭐ ELITE I',
    12: '⭐ ELITE II',
    13: '⭐ ELITE III',
    14: '⭐ ELITE IV',
    15: '⭐ ELITE V',
    16: '💫 MASTER I',
    17: '💫 MASTER II',
    18: '💫 MASTER III',
    19: '💫 MASTER IV',
    20: '💫 MASTER V',
}

# ==================== GAME CONSTANTS ====================
DAILY_AUTO = 200
PREMIUM_DAILY_AUTO = 400
DAILY_BASE = 1000
PREMIUM_DAILY_BASE = 1500
DAILY_MIN = 50
DAILY_MAX = 100
PREMIUM_DAILY_MIN = 100
PREMIUM_DAILY_MAX = 200

PROTECTION_COSTS = {
    1: 200,
    2: 450,
    3: 750
}

ROB_NORMAL_MIN = 80
ROB_NORMAL_MAX = 100
ROB_PROTECTED_MAX = 10
PREMIUM_ROB_MIN = 120
PREMIUM_ROB_MAX = 150

KILL_MIN = 50
KILL_MAX = 100
PREMIUM_KILL_MIN = 75
PREMIUM_KILL_MAX = 150

MEGA_ROB_PERCENT = 200
MEGA_KILL_PERCENT = 250
REVIVE_COST = 5000
GODMODE_COST = 1000

DEATH_DURATION = 24  # hours
SHIELD_DURATION = 1  # hour
PREMIUM_SHIELD_DURATION = 2  # hours
TAX_RATE = 10  # percent

PREMIUM_PRICES = {
    'in_1m': 90,
    'in_3m': 180,
    'in_6m': 270,
    'in_1y': 450,
    'us_1m': 1,
    'us_3m': 2,
    'us_6m': 3,
    'us_1y': 5,
}

# ==================== HELPER FUNCTIONS ====================
def calculate_tax(amount):
    tax = (amount * TAX_RATE) // 100
    after_tax = amount - tax
    return after_tax, tax

def add_tax_to_owner(tax_amount):
    owner_data = db.get_user(OWNER_ID)
    db.update_user(OWNER_ID, {
        'balance': owner_data['balance'] + tax_amount,
        'total_tax_collected': owner_data.get('total_tax_collected', 0) + tax_amount
    })

def format_number(num):
    if num >= 10000000:
        return f"{num/10000000:.1f}Cr"
    elif num >= 100000:
        return f"{num/100000:.1f}L"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def get_rank(user_balance, all_users_balances):
    sorted_users = sorted(all_users_balances, reverse=True)
    total_users = len(sorted_users)
    
    if total_users == 0:
        return "🥚 Egg"
    
    try:
        user_position = sorted_users.index(user_balance) + 1
    except:
        user_position = total_users
    
    percentile = (user_position / total_users) * 100
    
    if percentile <= 10:
        return "💫 God"
    elif percentile <= 20:
        return "🔥 Immortal"
    elif percentile <= 30:
        return "🕊️ Mythic"
    elif percentile <= 40:
        return "🌟 Legend"
    elif percentile <= 50:
        return "⚡ Emperor"
    elif percentile <= 60:
        return "👑 King"
    elif percentile <= 70:
        return "🐉 Dragon"
    elif percentile <= 80:
        return "🦁 Lion"
    elif percentile <= 85:
        return "🦅 Eagle"
    elif percentile <= 90:
        return "🐦 Bird"
    elif percentile <= 95:
        return "🐣 Chick"
    else:
        return "🥚 Egg"

def get_top_20_badge(position):
    return TOP_20_BADGES.get(position, "")

def is_premium(user_data):
    if not user_data.get('premium', False):
        return False
    if user_data.get('premium_expiry'):
        expiry = datetime.fromisoformat(user_data['premium_expiry'])
        if expiry < datetime.now():
            return False
    return True

# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id, user.username, user.first_name)
    
    all_balances = [data['balance'] for data in db.get_all_users().values()]
    rank = get_rank(user_data['balance'], all_balances)
    db.update_user(user.id, {'rank': rank})
    
    msg = f"""
╔════════════════════════════╗
║     👑 ROBBERY WORLD 👑    ║
╚════════════════════════════╝

💰 **YOUR STATS:**
• Balance: ${format_number(user_data['balance'])}
• Rank: {rank}
• Status: {'🟢 ALIVE' if user_data['status'] == 'alive' else '🔴 DEAD'}
• Premium: {'✅ YES' if is_premium(user_data) else '❌ NO'}

━━━━━━━━━━━━━━━━━━━
📋 **COMMANDS:**

💰 **ECONOMY**
/daily - Get daily bonus
/balance - Check balance
/pay @user amount - Send money
/gift @user - Send gift

🛡️ **PROTECTION**
/protect 1/2/3 - Buy protection
/mystatus - Your status

⚔️ **ATTACKS**
/rob @user - Rob someone
/kill @user - Kill someone
/revive @user - Revive dead (5000)

📊 **INFO**
/leaderboard - Group ranking
/leaderboard global - Global ranking
/details @user - User details
/mydetails - Your details

🎁 **GIFTS**
/gifts - All 30 gifts
/sendgift @user - Send gift

👑 **PREMIUM**
/premiumpreview - See premium features
/buypremium - Buy premium

━━━━━━━━━━━━━━━━━━━
🔥 Welcome to Robbery World!
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id, user.username, user.first_name)
    
    if user_data['status'] != 'alive':
        await update.message.reply_text("💀 You are dead! Wait for revive.")
        return
    
    last_daily = user_data.get('last_daily')
    if last_daily:
        last = datetime.fromisoformat(last_daily)
        if datetime.now() - last < timedelta(hours=20 if is_premium(user_data) else 24):
            remaining = timedelta(hours=20 if is_premium(user_data) else 24) - (datetime.now() - last)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await update.message.reply_text(f"⏳ Wait {hours}h {minutes}m for next daily!")
            return
    
    if is_premium(user_data):
        percent = random.randint(PREMIUM_DAILY_MIN, PREMIUM_DAILY_MAX)
        base = PREMIUM_DAILY_BASE
    else:
        percent = random.randint(DAILY_MIN, DAILY_MAX)
        base = DAILY_BASE
    
    bonus = (base * percent) // 100
    after_tax, tax = calculate_tax(bonus)
    
    new_balance = user_data['balance'] + after_tax
    streak = user_data.get('daily_streak', 0) + 1
    
    db.update_user(user.id, {
        'balance': new_balance,
        'last_daily': datetime.now().isoformat(),
        'daily_streak': streak,
        'total_earned': user_data.get('total_earned', 0) + after_tax
    })
    
    add_tax_to_owner(tax)
    
    msg = f"""
🎁 **DAILY BONUS** 🎁

• You got: **{percent}%**
• Amount: **${format_number(bonus)}**
• Tax (10%): **${format_number(tax)}**
• You received: **${format_number(after_tax)}**
• Streak: **{streak} days**
• New Balance: **${format_number(new_balance)}**

{'👑 Premium Bonus!' if is_premium(user_data) else ''}
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id, user.username, user.first_name)
    
    msg = f"""
💰 **YOUR WALLET** 💰

• Balance: **${format_number(user_data['balance'])}**
• Rank: **{user_data.get('rank', '🥚 Egg')}**
• Status: {'🟢 ALIVE' if user_data['status'] == 'alive' else '🔴 DEAD'}
• Premium: {'✅ YES' if is_premium(user_data) else '❌ NO'}

📊 **STATS:**
• Total Earned: **${format_number(user_data.get('total_earned', 0))}**
• Total Lost: **${format_number(user_data.get('total_lost', 0))}**
• Robs: **{user_data.get('rob_count', 0)}**
• Kills: **{user_data.get('kill_count', 0)}**
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = db.get_user(user.id, user.username, user.first_name)
    
    if user_data['status'] != 'alive':
        await update.message.reply_text("💀 Dead people can't buy protection!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /protect [days]\n1 day=$200, 2 days=$450, 3 days=$750")
        return
    
    try:
        days = int(context.args[0])
        if days not in PROTECTION_COSTS:
            await update.message.reply_text("Choose 1, 2, or 3 days only!")
            return
    except:
        await update.message.reply_text("Invalid input! Use /protect 1/2/3")
        return
    
    if user_data['protection']['active']:
        expiry = datetime.fromisoformat(user_data['protection']['expiry'])
        if expiry > datetime.now():
            remaining = expiry - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            await update.message.reply_text(f"🛡️ Already protected! Expires in {hours}h")
            return
    
    cost = PROTECTION_COSTS[days]
    
    if is_premium(user_data):
        cost = int(cost * 0.9)
    
    if user_data['balance'] < cost:
        await update.message.reply_text(f"❌ Need ${format_number(cost)}!")
        return
    
    after_tax, tax = calculate_tax(cost)
    expiry = datetime.now() + timedelta(days=days)
    new_balance = user_data['balance'] - cost
    
    db.update_user(user.id, {
        'balance': new_balance,
        'protection': {
            'active': True,
            'expiry': expiry.isoformat(),
            'days': days
        }
    })
    
    add_tax_to_owner(tax)
    
    await update.message.reply_text(
        f"🛡️ **PROTECTION ACTIVE**\n\n"
        f"Days: {days}\n"
        f"Cost: ${format_number(cost)}\n"
        f"Tax: ${format_number(tax)}\n"
        f"Expires: {expiry.strftime('%Y-%m-%d %H:%M')}\n"
        f"Balance left: ${format_number(new_balance)}"
    )

async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    attacker = db.get_user(user.id, user.username, user.first_name)
    
    if attacker['status'] != 'alive':
        await update.message.reply_text("💀 You are dead!")
        return
    
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("Reply to user or tag them: /rob @user")
        return
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        username = context.args[0].replace('@', '')
        target = None
        try:
            async for member in context.bot.get_chat_administrators(update.effective_chat.id):
                if member.user.username and member.user.username.lower() == username.lower():
                    target = member.user
                    break
        except:
            await update.message.reply_text("User not found!")
            return
    
    if not target or target.id == user.id:
        await update.message.reply_text("Invalid target!")
        return
    
    target_data = db.get_user(target.id, target.username, target.first_name)
    
    if target_data['status'] != 'alive':
        await update.message.reply_text("💀 Target is dead!")
        return
    
    last_attacked = target_data.get('last_attacked')
    if last_attacked:
        last = datetime.fromisoformat(last_attacked)
        shield_hours = PREMIUM_SHIELD_DURATION if is_premium(target_data) else SHIELD_DURATION
        if datetime.now() - last < timedelta(hours=shield_hours):
            remaining = timedelta(hours=shield_hours) - (datetime.now() - last)
            minutes = int(remaining.total_seconds() // 60)
            await update.message.reply_text(f"🛡️ {target.first_name} has shield! Wait {minutes}m")
            return
    
    premium_attacker = is_premium(attacker)
    
    if target_data['protection']['active']:
        if premium_attacker:
            max_rob = (target_data['balance'] * 15) // 100
        else:
            max_rob = (target_data['balance'] * ROB_PROTECTED_MAX) // 100
        
        if max_rob <= 0:
            await update.message.reply_text("💰 Target has no money!")
            return
        rob_amount = random.randint(1, max_rob)
        prot_msg = " (Protected)"
    else:
        if premium_attacker:
            min_rob = (target_data['balance'] * PREMIUM_ROB_MIN) // 100
            max_rob = (target_data['balance'] * PREMIUM_ROB_MAX) // 100
        else:
            min_rob = (target_data['balance'] * ROB_NORMAL_MIN) // 100
            max_rob = (target_data['balance'] * ROB_NORMAL_MAX) // 100
        
        if max_rob <= 0:
            await update.message.reply_text("💰 Target has no money!")
            return
        rob_amount = random.randint(min_rob, max_rob)
        prot_msg = ""
    
    after_tax, tax = calculate_tax(rob_amount)
    
    new_attacker = attacker['balance'] + after_tax
    new_target = target_data['balance'] - rob_amount
    
    db.update_user(user.id, {
        'balance': new_attacker,
        'rob_count': attacker.get('rob_count', 0) + 1,
        'total_earned': attacker.get('total_earned', 0) + after_tax
    })
    
    db.update_user(target.id, {
        'balance': new_target,
        'last_attacked': datetime.now().isoformat(),
        'total_lost': target_data.get('total_lost', 0) + rob_amount
    })
    
    add_tax_to_owner(tax)
    
    msg = f"""
🔫 **ROB SUCCESSFUL** 🔫

• Attacker: {user.first_name}
• Target: {target.first_name}
• Robbed: **${format_number(rob_amount)}**{prot_msg}
• Tax (10%): **${format_number(tax)}**
• You got: **${format_number(after_tax)}**

🛡️ Target has {PREMIUM_SHIELD_DURATION if is_premium(target_data) else SHIELD_DURATION}h shield!
    """
    await update.message.reply_text(msg)

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    killer = db.get_user(user.id, user.username, user.first_name)
    
    if killer['status'] != 'alive':
        await update.message.reply_text("💀 You are dead!")
        return
    
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text("Reply to user or tag them: /kill @user")
        return
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        username = context.args[0].replace('@', '')
        target = None
        try:
            async for member in context.bot.get_chat_administrators(update.effective_chat.id):
                if member.user.username and member.user.username.lower() == username.lower():
                    target = member.user
                    break
        except:
            await update.message.reply_text("User not found!")
            return
    
    if not target or target.id == user.id:
        await update.message.reply_text("Invalid target!")
        return
    
    target_data = db.get_user(target.id, target.username, target.first_name)
    
    if target_data['status'] != 'alive':
        await update.message.reply_text("💀 Target already dead!")
        return
    
    last_attacked = target_data.get('last_attacked')
    if last_attacked:
        last 
