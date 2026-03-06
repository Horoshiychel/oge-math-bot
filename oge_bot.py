import json, logging, random, ssl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# 🔥 SSL ФИКС (обязательно!)
ssl._create_default_https_context = ssl._create_unverified_context


# Функция очистки текста для Telegram
def clean_text(text):
    """Убирает проблемные символы"""
    if not text:
        return "Нет ответа от GigaChat"
    replacements = {'*': '', '_': '', '`': '', '\\': '', '[': '', ']': '',
                    '(': '', ')': '', '<': '', '>': ''}
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.strip()[:3500]


# Конфигурация
import os
BOT_TOKEN = os.getenv("8650646242:AAF4HfvILHLFfsJgFeBZYt5D9PjOkxfh6ds")
GIGACHAT_TOKEN = os.getenv("MDE5Y2JjYTktMjg5OC03Mzg4LWI2ZjEtMjE2ZjFiYzFkZWNlOjc5Nzk5NDIyLTkwOWYtNDFiMy1iZGJhLThkZGZhYjIzOTlhZg==")


    GIGACHAT_AVAILABLE = bool(GIGACHAT_TOKEN and GIGACHAT_TOKEN.strip())
    print(f"✅ Config: BOT_TOKEN=✓, GigaChat={'✓' if GIGACHAT_AVAILABLE else '✗'}")
except:
    GIGACHAT_AVAILABLE = False

# GigaChat (ПРАВИЛЬНАЯ инициализация)
giga = None
if GIGACHAT_AVAILABLE:
    try:
        from gigachat import GigaChat

        giga = GigaChat(credentials=GIGACHAT_TOKEN, verify_ssl_certs=False)
        print("✅ GigaChat готов!")
    except Exception as e:
        print(f"❌ GigaChat: {e}")
        giga = None

# Загрузка задач
print("📚 Загружаем tasks.json...")
try:
    with open("tasks.json", "r", encoding="utf-8") as f:
        TASKS = json.load(f)
    total_tasks = sum(len(tasks) for tasks in TASKS.values())
    print(f"✅ {total_tasks} задач загружено!")
except:
    TASKS = {}
    total_tasks = 0

user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📐 Геометрия", callback_data="геометрия"),
         InlineKeyboardButton("🔢 Алгебра", callback_data="алгебра")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    ai_status = "🧠 GigaChat ✅" if giga else "📚 JSON"

    await update.message.reply_text(
        f"🤖 *ОГЭ Математика Helper*\n\n"
        f"📚 {total_tasks} задач\n"
        f"{ai_status}\n\n"
        f"*Схема:* тест → JSON решение → GigaChat разбор",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        if query.data in TASKS:  # 1️⃣ ТЕСТ
            if user_id not in user_data:
                user_data[user_id] = {"stats": {"correct": 0, "total": 0}}

            task = random.choice(TASKS[query.data])
            user_data[user_id]["current_task"] = task

            keyboard = [
                [InlineKeyboardButton(f"{chr(65 + i)}. {opt}", callback_data=f"ans_{i}")
                 for i, opt in enumerate(task["options"])],
                [InlineKeyboardButton("❓ Подсказка", callback_data="hint")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📝 *Задача #{task['id']} ({query.data.title()})*\n\n"
                f"{task['question']}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        elif query.data.startswith("ans_"):  # 2️⃣ JSON РЕШЕНИЕ
            answer_idx = int(query.data.split("_")[1])
            task = user_data[user_id]["current_task"]
            stats = user_data[user_id]["stats"]

            stats["total"] += 1
            correct = answer_idx == task["answer"]
            if correct:
                stats["correct"] += 1

            theme = next(iter(TASKS)) if TASKS else "геометрия"
            keyboard = [
                [InlineKeyboardButton("🤖 GigaChat разбор", callback_data="giga")],
                [InlineKeyboardButton("➡️ Новая задача", callback_data=theme),
                 InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            result = "✅ *Правильно!*" if correct else f"❌ *Ответ:* {chr(65 + task['answer'])}"

            await query.edit_message_text(
                f"{result}\n\n"
                f"📋 *Решение из базы:*\n`{task['solution']}`\n\n"
                f"_🔥 GigaChat разберёт ПОШАГОВО ниже!_",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        elif query.data == "giga":  # 3️⃣ 🔥 GIGAchat (ФИНАЛЬНАЯ ВЕРСИЯ)
            task = user_data[user_id]["current_task"]
            await query.edit_message_text("🤖 GigaChat репетитор анализирует... ⏳")

            if giga:
                try:
                    # 🔥 ПРАВИЛЬНЫЙ GigaChat API — ПРОСТАЯ СТРОКА!
                    response = giga.chat(f"""ОГЭ Математика 9 класс. Репетитор.

ЗАДАЧА: {task['question']}
ПРАВИЛЬНЫЙ ОТВЕТ: {task['options'][task['answer']]}

Разбери ПОШАГОВО:
1. Что спрашивают?
2. Какая формула?
3. Расчёт с числами
4. Проверка результата  
5. Почему этот ответ?

Кратко и просто для школьника!""")

                    # 🔥 ПРАВИЛЬНЫЙ доступ к ответу GigaChat
                    explanation = clean_text(response.choices[0].message.content)

                    keyboard = [
                        [InlineKeyboardButton("➡️ Новая задача", callback_data="геометрия")],
                        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
                         InlineKeyboardButton("🏠 Меню", callback_data="menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await query.edit_message_text(
                        f"🤖 *GigaChat ОГЭ-репетитор:*\n\n{explanation}",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )

                except Exception as e:
                    error_text = f"🤖 GigaChat ошибка:\n`{str(e)[:100]}`\n\n📋 Резерв: {task['solution']}"
                    await query.edit_message_text(error_text, parse_mode="Markdown")
            else:
                keyboard = [
                    [InlineKeyboardButton("➡️ Новая задача", callback_data="геометрия")],
                    [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
                     InlineKeyboardButton("🏠 Меню", callback_data="menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"🤖 GigaChat недоступен\n\n📋 `{task['solution']}`",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

        elif query.data == "stats":  # 4️⃣ СТАТИСТИКА
            stats = user_data.get(user_id, {}).get("stats", {"correct": 0, "total": 0})
            percent = (stats["correct"] / max(stats["total"], 1) * 100)

            keyboard = [[InlineKeyboardButton("🏠 Меню", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📊 *Статистика ОГЭ:*\n\n"
                f"✅ `{stats['correct']}/{stats['total']}`\n"
                f"📈 *{percent:.1f}%*\n\n"
                f"_🎯 Цель: 90%+ !_",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        elif query.data == "hint":  # 5️⃣ ПОДСКАЗКА
            task = user_data[user_id]["current_task"]
            keyboard = [
                [InlineKeyboardButton(f"{chr(65 + i)}. {opt}", callback_data=f"ans_{i}")
                 for i, opt in enumerate(task["options"])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"💡 *Подсказка:*\n`{task['solution'][:150]}...`\n\n"
                f"_Выбери ответ!_",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        elif query.data == "menu":  # 6️⃣ МЕНЮ
            await start(update, context)

    except BadRequest as e:
        print(f"❌ Telegram: {e}")
        await query.edit_message_text("❌ Ошибка. /start")
    except Exception as e:
        print(f"❌ Ошибка {query.data}: {e}")
        await query.edit_message_text("❌ /start")


if __name__ == "__main__":
    print("🚀 ОГЭ-бот + GigaChat (ФИНАЛЬНАЯ ВЕРСИЯ)")
    print(f"📊 Задач: {total_tasks}")
    print(f"🤖 GigaChat: {'✅' if giga else '❌'}")

    if 'BOT_TOKEN' not in globals() or not BOT_TOKEN:
        print("❌ Нет BOT_TOKEN!")
        exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("✅ Запущен! Telegram → /start")
    print("🎯 Тест → JSON → GigaChat ✅")
    app.run_polling(drop_pending_updates=True)
