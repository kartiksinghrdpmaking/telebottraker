import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Load Env ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = 1708011472  # Replace with your Telegram ID

# === DB ===
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    category TEXT,
    timestamp TEXT
)''')
conn.commit()

def is_authorized(user_id):
    return user_id == ALLOWED_USER_ID

# === Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. You ain't Kartik.")
        return
    await update.message.reply_text("💸 Expense Tracker Bot is live!\nUse /spent <amount> <category> to log.")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your User ID: {update.effective_user.id}")

async def spent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    try:
        amount = float(context.args[0])
        category = " ".join(context.args[1:])
        if not category:
            raise ValueError
    except:
        await update.message.reply_text("⚠️ Usage: /spent <amount> <category>")
        return

    cursor.execute("INSERT INTO expenses (user_id, amount, category, timestamp) VALUES (?, ?, ?, ?)", (
        update.effective_user.id, amount, category, datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"✅ ₹{amount} spent on {category}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    today = datetime.now().date()
    cursor.execute("SELECT amount, category FROM expenses WHERE user_id=? AND DATE(timestamp)=?",
                   (update.effective_user.id, today.isoformat()))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No expenses today. Your wallet's proud 🤑")
        return

    total = sum(row[0] for row in rows)
    breakdown = {}
    for amount, category in rows:
        breakdown[category] = breakdown.get(category, 0) + amount

    breakdown_text = "\n".join([f"• {cat}: ₹{amt:.2f}" for cat, amt in breakdown.items()])
    await update.message.reply_text(f"💰 Today's Spending: ₹{total:.2f}\n\n{breakdown_text}")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    last_week = datetime.now() - timedelta(days=7)
    cursor.execute("SELECT amount, category FROM expenses WHERE user_id=? AND timestamp >= ?",
                   (update.effective_user.id, last_week.isoformat()))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No expenses in the last 7 days. Legend.")
        return

    total = sum(row[0] for row in rows)
    breakdown = {}
    for amount, category in rows:
        breakdown[category] = breakdown.get(category, 0) + amount

    breakdown_text = "\n".join([f"• {cat}: ₹{amt:.2f}" for cat, amt in breakdown.items()])
    await update.message.reply_text(f"📆 Last 7 Days Spending: ₹{total:.2f}\n\n{breakdown_text}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    cursor.execute("DELETE FROM expenses WHERE user_id=?", (update.effective_user.id,))
    conn.commit()
    await update.message.reply_text("🧹 All your expense logs have been wiped. Start fresh!")

# === App Init ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("myid", myid))
app.add_handler(CommandHandler("spent", spent))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("weekly", weekly))
app.add_handler(CommandHandler("reset", reset))

print("Expense Tracker Bot running...")
app.run_polling()
