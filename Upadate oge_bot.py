import json, random, ssl, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

ssl._create_default_https_context = ssl._create_unverified_context

def clean_text(text):
    if not text: return "Нет ответа"
    replacements = {
        '*': '', '_': '', '`': '', '\\': '',
        '[': ' ', ']': ' ', '(': ' ', ')': ' ',
        '<': ' ', '>': ' '
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.strip()[:3500]

BOT_TOKEN = os.getenv("BOT_TOKEN")
GIGACHAT_TOKEN = os.getenv("GIGACHAT_TOKEN")

try:
    from gigachat import GigaChat
    giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False) if GIGACHAT_TOKEN else None
except:
    giga = None

try:
    with open("tasks.json", "r", encoding="utf-8") as f:
        TASKS = json.load(f)
    total_tasks = sum(len(tasks) for tasks in TASKS.values())
except:
    TASKS, total_tasks = {}, 0

user_data = {}

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("📐 Геометрия", callback_data="геометрия"), 
         InlineKeyboardButton("🔢 Алгебра", callback_data="алгебра")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ai_status = "🧠 GigaChat ✅" if giga else "📚 JSON"
    await update.message.reply_text(
        f"🤖 *ОГЭ Математика Helper*\n\n📚 {total_tasks} задач\n{ai_status}",
        parse_mode="Markdown", reply_markup=reply_markup
    )

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data in TASKS:
        task = random.choice(TASKS[query.data])
        user_data[user_id] = {"current_task": task, "stats": user_data.get(user_id, {}).get("stats", {"correct": 0, "total": 0})}
        
        keyboard = [[InlineKeyboardButton(f"{chr(65+i)}. {opt}", callback_data=f"ans_{i}") 
                    for i, opt in enumerate(task["options"])], 
                   [InlineKeyboardButton("❓ Подсказка", callback_data="hint")]]
        await query.edit_message_text(
            f"📝 *Задача #{task['id']} ({query.data.title()})*\n\n{task['question']}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("ans_"):
        answer_idx = int(query.data.split("_")[1])
        task = user_data[user_id]["current_task"]
        stats = user_data[user_id]["stats"]
        stats["total"] += 1
        correct = answer_idx == task["answer"]
        if correct: stats["correct"] += 1
        
        keyboard = [
            [InlineKeyboardButton("🤖 GigaChat", callback_data="giga")],
            [InlineKeyboardButton("➡️ Новая", callback_data="геометрия"),
             InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
        ]
        result = "✅ *Правильно!*" if correct else f"❌ *Ответ:* {chr(65+task['answer'])}"
        await query.edit_message_text(
            f"{result}\n\n📋 *Решение:*\n`{task['solution']}`\n\n_🔥 GigaChat разберёт подробно!_",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

if __name__ == "__main__":
    print("🚀 ОГЭ-бот запущен!")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
    else:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button))
        app.run_polling(drop_pending_updates=True)
