import json, logging, random, ssl, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

ssl._create_default_https_context = ssl._create_unverified_context

def clean_text(text):
    if not text: return "Нет ответа"
    replacements = {'*':'','_':'','`':'','\\':'','[':' ',']':' ','(':')':' ','<':'>':''}
    for bad, good in replacements.items(): text = text.replace(bad, good)
    return text.strip()[:3500]

BOT_TOKEN = os.getenv("BOT_TOKEN")
GIGACHAT_TOKEN = os.getenv("MDE5Y2JjYTktMjg5OC03Mzg4LWI2ZjEtMjE2ZjFiYzFkZWNlOjc5Nzk5NDIyLTkwOWYtNDFiMy1iZGJhLThkZGZhYjIzOTlhZg==")
GIGACHAT_AVAILABLE = bool(GIGACHAT_TOKEN and GIGACHAT_TOKEN.strip())

giga = None
if GIGACHAT_AVAILABLE:
    try:
        from gigachat import GigaChat
        giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False)
    except: giga = None

try:
    with open("tasks.json", "r", encoding="utf-8") as f:
        TASKS = json.load(f)
    total_tasks = sum(len(tasks) for tasks in TASKS.values())
except: TASKS, total_tasks = {}, 0

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📐 Геометрия", callback_data="геометрия"), InlineKeyboardButton("🔢 Алгебра", callback_data="алгебра")],[InlineKeyboardButton("📊 Статистика", callback_data="stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ai_status = "🧠 GigaChat ✅" if giga else "📚 JSON"
    await update.message.reply_text(f"🤖 *ОГЭ Helper*\n\n📚 {total_tasks} задач\n{ai_status}", parse_mode="Markdown", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        if query.data in TASKS:
            if user_id not in user_data: user_data[user_id] = {"stats": {"correct": 0, "total": 0}}
            task = random.choice(TASKS[query.data])
            user_data[user_id]["current_task"] = task
            keyboard = [[InlineKeyboardButton(f"{chr(65+i)}. {opt}", callback_data=f"ans_{i}") for i, opt in enumerate(task["options"])], [InlineKeyboardButton("❓ Подсказка", callback_data="hint")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"📝 *#{task['id']} ({query.data.title()})*\n\n{task['question']}", parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data.startswith("ans_"):
            answer_idx = int(query.data.split("_")[1])
            task = user_data[user_id]["current_task"]
            stats = user_data[user_id]["stats"]
            stats["total"] += 1
            correct = answer_idx == task["answer"]
            if correct: stats["correct"] += 1
            theme = next(iter(TASKS)) if TASKS else "геометрия"
            keyboard = [[InlineKeyboardButton("🤖 GigaChat", callback_data="giga")],[InlineKeyboardButton("➡️ Новая", callback_data=theme), InlineKeyboardButton("📊 Статистика", callback_data="stats")],[InlineKeyboardButton("🏠 Меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            result = "✅ *Правильно!*" if correct else f"❌ *Ответ:* {chr(65+task['answer'])}"
            await query.edit_message_text(f"{result}\n\n📋 *Решение:*\n`{task['solution']}`\n\n_🔥 GigaChat разберёт!_", parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "giga":
            task = user_data[user_id]["current_task"]
            await query.edit_message_text("🤖 GigaChat репетитор... ⏳")
            if giga:
                try:
                    response = giga.chat(f"""ОГЭ Математика 9 класс.

ЗАДАЧА: {task['question']}
ОТВЕТ: {task['options'][task['answer']]}

5 ШАГОВ:
1. Что спрашивают?
2. Формула
3. Расчёт
4. Проверка
5. Почему верный?

Кратко для школьника!""")
                    explanation = clean_text(response.choices[0].message.content)
                    keyboard = [[InlineKeyboardButton("➡️ Новая", callback_data="геометрия")],[InlineKeyboardButton("📊 Статистика", callback_data="stats"), InlineKeyboardButton("🏠 Меню", callback_data="menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(f"🤖 *GigaChat:*\n\n{explanation}", parse_mode="Markdown", reply_markup=reply_markup)
                except Exception as e:
                    await query.edit_message_text(f"🤖 GigaChat недоступен\n\n📋 `{task['solution']}`", parse_mode="Markdown")
            else:
                await query.edit_message_text(f"🤖 GigaChat не настроен\n\n📋 `{task['solution']}`", parse_mode="Markdown")
        
        elif query.data == "stats":
            stats = user_data.get(user_id, {}).get("stats", {"correct": 0, "total": 0})
            percent = (stats["correct"] / max(stats["total"], 1) * 100)
            keyboard = [[InlineKeyboardButton("🏠 Меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"📊 *Статистика:*\n\n✅ `{stats['correct']}/{stats['total']}`\n📈 *{percent:.1f}%*\n\n_🎯 Цель: 90%+ !_", parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "hint":
            task = user_data[user_id]["current_task"]
            keyboard = [[InlineKeyboardButton(f"{chr(65+i)}. {opt}", callback_data=f"ans_{i}") for i, opt in enumerate(task["options"])]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"💡 *Подсказка:*\n`{task['solution'][:150]}...`\n\n_Выбери ответ!_", parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "menu": await start(update, context)
    
    except Exception as e: await query.edit_message_text("❌ /start")

if __name__ == "__main__":
    print("🚀 ОГЭ-бот запущен!")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling(drop_pending_updates=True)
