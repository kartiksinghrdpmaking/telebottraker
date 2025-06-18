# main.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from datetime import timedelta
# === DB SETUP ===
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

# === COMMAND FUNCTIONS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo Kartik! Tracker Bot Online ✅")
from datetime import timedelta

async def weeksummary(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def log_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, log_type):
    content = " ".join(context.args)
    if not content:
        await update.message.reply_text("Bhai kuch toh likho 😭")
        return
    cursor.execute("INSERT INTO logs (user_id, type, content, timestamp) VALUES (?, ?, ?, ?)", (
        update.effective_user.id, log_type, content, datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"Logged your {log_type}: {content}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT type, content, timestamp FROM logs WHERE user_id=? ORDER BY timestamp DESC LIMIT 10", 
                   (update.effective_user.id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No logs found, Kartik. You slacking again? 🤡")
    else:
        summary_text = "\n".join([f"🕒 {r[2][:16]} - [{r[0]}] {r[1]}" for r in rows])
        await update.message.reply_text("📊 Last 10 Logs:\n" + summary_text)

# === BOT SETUP ===
app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

# === COMMANDS ===
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("logstudy", lambda u, c: log_entry(u, c, "Study")))
app.add_handler(CommandHandler("logproject", lambda u, c: log_entry(u, c, "Project")))
app.add_handler(CommandHandler("braindump", lambda u, c: log_entry(u, c, "BrainDump")))
app.add_handler(CommandHandler("wasted", lambda u, c: log_entry(u, c, "WastedTime")))
app.add_handler(CommandHandler("mood", lambda u, c: log_entry(u, c, "Mood")))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("weeksummary", weeksummary))


print("Bot running...")
app.run_polling()
