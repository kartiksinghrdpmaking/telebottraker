import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Load Environment Variables ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Secure Access ===
ALLOWED_USER_ID = 1708011472  # Replace this with YOUR Telegram ID

# === DB Setup ===
conn = sqlite3.connect("kartik_tracker.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    content TEXT,
    timestamp TEXT
)''')
conn.commit()

# === Auth Check ===
def is_authorized(user_id):
    return user_id == ALLOWED_USER_ID

# === Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. You ain't Kartik.")
        return
    await update.message.reply_text("Yo Kartik! Tracker Bot Online ✅")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your User ID: {update.effective_user.id}")

async def log_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, log_type):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. You ain't Kartik.")
        return
    content = " ".join(context.args)
    if not content:
        await update.message.reply_text("Bhai kuch toh likho 😭")
        return
    cursor.execute("INSERT INTO logs (user_id, type, content, timestamp) VALUES (?, ?, ?, ?)", (
        update.effective_user.id, log_type, content, datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"✅ Logged [{log_type}]: {content}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. You ain't Kartik.")
        return
    cursor.execute("SELECT type, content, timestamp FROM logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
                   (update.effective_user.id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No logs found, Kartik. You slacking again? 🤡")
    else:
        summary_text = "\n".join([f"🕒 {r[2][:16]} - [{r[0]}] {r[1]}" for r in rows])
        await update.message.reply_text("📊 Last 10 Logs:\n" + summary_text)

async def weeksummary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access denied. You ain't Kartik.")
        return
    one_week_ago = datetime.now() - timedelta(days=7)
    cursor.execute(
        "SELECT type, content, timestamp FROM logs WHERE user_id=? AND timestamp >= ? ORDER BY timestamp DESC",
        (update.effective_user.id, one_week_ago.isoformat())
    )
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No logs from the past week. Either you're slacking, or lying. 🤥")
    else:
        summary_text = "\n".join([f"🗓 {r[2][:16]} - [{r[0]}] {r[1]}" for r in rows])
        await update.message.reply_text("📅 Your Last 7 Days Activity:\n" + summary_text)

# === App ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# === Command Handlers ===
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("myid", myid))
app.add_handler(CommandHandler("logstudy", lambda u, c: log_entry(u, c, "Study")))
app.add_handler(CommandHandler("logproject", lambda u, c: log_entry(u, c, "Project")))
app.add_handler(CommandHandler("braindump", lambda u, c: log_entry(u, c, "BrainDump")))
app.add_handler(CommandHandler("wasted", lambda u, c: log_entry(u, c, "WastedTime")))
app.add_handler(CommandHandler("mood", lambda u, c: log_entry(u, c, "Mood")))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("weeksummary", weeksummary))

print("Bot running...")
app.run_polling()
