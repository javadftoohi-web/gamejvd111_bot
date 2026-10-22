import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from db import init_db, get_profile, leaderboard
from games import CATALOG, GAME_CATEGORIES, play_quiz, play_rps, play_guess, start_group_quiz, answer_group_quiz

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
MINI_APP_URL = os.getenv("MINI_APP_URL", "").strip()

def main_menu():
    rows = [
        [InlineKeyboardButton("🎮 همه بازی‌ها", callback_data="catalog")],
        [InlineKeyboardButton("👥 شروع چالش گروهی", callback_data="groupquiz_start")],
        [InlineKeyboardButton("🏆 جدول امتیاز", callback_data="leaderboard"),
         InlineKeyboardButton("👤 پروفایل من", callback_data="profile")],
    ]
    if MINI_APP_URL.startswith("https://"):
        rows.insert(0, [InlineKeyboardButton("🕹️ ورود به Game Hub", web_app=WebAppInfo(url=MINI_APP_URL))])
    return InlineKeyboardMarkup(rows)

def catalog_keyboard():
    rows = []
    for category, game_ids in GAME_CATEGORIES.items():
        rows.append([InlineKeyboardButton(f"{category} ({len(game_ids)})", callback_data=f"cat:{category}")])
    rows.append([InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home")])
    return InlineKeyboardMarkup(rows)

def game_keyboard(category):
    rows = []
    for game_id in GAME_CATEGORIES.get(category, []):
        item = CATALOG[game_id]
        status = "✅" if item["status"] == "implemented" else "🛠️"
        rows.append([InlineKeyboardButton(f"{status} {item['name']}", callback_data=f"game:{game_id}")])
    rows.append([InlineKeyboardButton("⬅️ دسته‌ها", callback_data="catalog")])
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎮 به Game Hub فارسی خوش آمدی!\n"
        "بازی انتخاب کن، امتیاز جمع کن و با اعضای گروه رقابت کن.\n\n"
        "علامت ✅ یعنی بازی در این نسخه پیاده‌سازی شده؛ 🛠️ یعنی در فهرست توسعه است.",
        reply_markup=main_menu()
    )

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("دسته بازی‌ها:", reply_markup=catalog_keyboard())

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = leaderboard(10)
    if not rows:
        await update.effective_message.reply_text("هنوز امتیازی ثبت نشده است.")
        return
    lines = ["🏆 برترین بازیکنان"]
    for i, p in enumerate(rows, 1):
        name = ("@" + p["username"]) if p["username"] else (p["first_name"] or "بازیکن")
        lines.append(f"{i}. {name} — {p['points']} امتیاز | {p['wins']} برد")
    await update.effective_message.reply_text("\n".join(lines), reply_markup=main_menu())

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_profile(update.effective_user)
    await update.effective_message.reply_text(
        f"👤 {p['first_name']}\n⭐ امتیاز: {p['points']}\n🏅 برد: {p['wins']}\n🎮 بازی: {p['games']}",
        reply_markup=main_menu()
    )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user = q.from_user

    if data == "home":
        await q.edit_message_text("🎮 منوی اصلی", reply_markup=main_menu())
    elif data == "catalog":
        await q.edit_message_text("دسته بازی‌ها:\n✅ پیاده‌سازی شده | 🛠️ در برنامه توسعه", reply_markup=catalog_keyboard())
    elif data.startswith("cat:"):
        category = data.split(":", 1)[1]
        await q.edit_message_text(f"🎮 {category}", reply_markup=game_keyboard(category))
    elif data == "leaderboard":
        rows = leaderboard(10)
        lines = ["🏆 برترین بازیکنان"]
        for i, p in enumerate(rows, 1):
            name = ("@" + p["username"]) if p["username"] else (p["first_name"] or "بازیکن")
            lines.append(f"{i}. {name} — {p['points']} امتیاز")
        await q.edit_message_text("\n".join(lines) if rows else "هنوز امتیازی ثبت نشده.", reply_markup=main_menu())
    elif data == "profile":
        p = get_profile(user)
        await q.edit_message_text(f"👤 {p['first_name']}\n⭐ امتیاز: {p['points']}\n🏅 برد: {p['wins']}\n🎮 بازی: {p['games']}", reply_markup=main_menu())
    elif data == "groupquiz_start":
        chat_id = q.message.chat_id
        result = start_group_quiz(chat_id, user.id)
        buttons = [[InlineKeyboardButton(text, callback_data=f"gq:{i}") for i, text in enumerate(result["options"])]]
        await q.edit_message_text(
            "👥 چالش اطلاعات عمومی گروه\n\n" + result["question"] + "\n\n"
            "هر عضو می‌تواند یک گزینه انتخاب کند. در این نسخه، دور گروهی با رأی اول هر کاربر ثبت می‌شود.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        context.chat_data["active_group_quiz"] = result
    elif data.startswith("gq:"):
        active = context.chat_data.get("active_group_quiz")
        if not active:
            await q.answer("چالش فعال نیست یا تمام شده.", show_alert=True)
            return
        choice = int(data.split(":")[1])
        result = answer_group_quiz(q.message.chat_id, user, choice, active)
        if result["duplicate"]:
            await q.answer("رأی تو قبلاً ثبت شده.", show_alert=True)
        else:
            await q.answer("رأی ثبت شد!")
            if result["correct"]:
                await q.message.reply_text(f"🎉 {user.first_name} پاسخ درست داد و ۵ امتیاز گرفت!")
            if result["finished"]:
                context.chat_data.pop("active_group_quiz", None)
                await q.message.reply_text("دور این سؤال بسته شد.")
    elif data.startswith("game:"):
        game_id = data.split(":", 1)[1]
        if game_id == "quiz":
            result = play_quiz(user)
            buttons = [[InlineKeyboardButton(f"{i+1}. {opt}", callback_data=f"quizans:{result['qid']}:{i}") for i, opt in enumerate(result["options"])]]
            await q.edit_message_text("🧠 " + result["question"], reply_markup=InlineKeyboardMarkup(buttons))
        elif game_id == "rps":
            await q.edit_message_text("✊ سنگ، کاغذ، قیچی", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("سنگ", callback_data="rps:rock"),
                InlineKeyboardButton("کاغذ", callback_data="rps:paper"),
                InlineKeyboardButton("قیچی", callback_data="rps:scissors")
            ]]))
        elif game_id == "guess":
            result = play_guess(user)
            context.user_data["guess"] = result["number"]
            await q.edit_message_text("🔢 یک عدد از ۱ تا ۵ انتخاب کن:", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(str(i), callback_data=f"guess:{i}") for i in range(1, 6)
            ]]))
        else:
            item = CATALOG[game_id]
            await q.edit_message_text(
                f"🛠️ {item['name']}\n\nاین بازی در نقشه راه نسخه توسعه قرار دارد و هنوز در این بسته قابل بازی نیست.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ برگشت به دسته‌ها", callback_data="catalog")]])
            )
    elif data.startswith("quizans:"):
        _, qid, answer = data.split(":")
        from games import submit_quiz
        result = submit_quiz(user, qid, int(answer))
        await q.edit_message_text(result["message"], reply_markup=main_menu())
    elif data.startswith("rps:"):
        result = play_rps(user, data.split(":")[1])
        await q.edit_message_text(result, reply_markup=main_menu())
    elif data.startswith("guess:"):
        guess = context.user_data.pop("guess", None)
        if guess is None:
            await q.edit_message_text("این دور تمام شده؛ دوباره شروع کن.", reply_markup=main_menu())
        elif int(data.split(":")[1]) == guess:
            from db import add_result
            add_result(user, 5, True)
            await q.edit_message_text(f"🎉 درست بود! عدد {guess} بود؛ ۵ امتیاز گرفتی.", reply_markup=main_menu())
        else:
            from db import add_result
            add_result(user, 0, False)
            await q.edit_message_text(f"عدد درست {guess} بود. دوباره امتحان کن!", reply_markup=main_menu())

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "منوی اصلی"),
        BotCommand("games", "فهرست بازی‌ها"),
        BotCommand("top", "جدول امتیاز"),
        BotCommand("profile", "پروفایل من"),
    ])

def main():
    if not TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in environment secrets.")
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("games", games))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(callback))
    logging.info("Game Hub bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
