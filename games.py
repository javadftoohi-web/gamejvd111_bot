import random
import uuid
from db import add_result, connect

CATALOG = {
    "quiz": {"name":"اطلاعات عمومی", "status":"implemented"},
    "word": {"name":"حدس کلمه", "status":"planned"},
    "riddle": {"name":"حل معما", "status":"planned"},
    "character": {"name":"حدس شخصیت", "status":"planned"},
    "flag": {"name":"حدس پرچم کشور", "status":"planned"},
    "math": {"name":"چالش ریاضی", "status":"planned"},
    "truefalse": {"name":"درست یا غلط", "status":"planned"},
    "proverb": {"name":"تکمیل ضرب‌المثل", "status":"planned"},
    "rps": {"name":"سنگ‌کاغذقیچی", "status":"implemented"},
    "tictactoe": {"name":"دوز", "status":"planned"},
    "guess": {"name":"حدس عدد", "status":"implemented"},
    "wordwar": {"name":"جنگ کلمات", "status":"planned"},
    "fastmath": {"name":"محاسبه سریع", "status":"planned"},
    "duelword": {"name":"حدس کلمه دونفره", "status":"planned"},
    "mafia": {"name":"مافیا", "status":"planned"},
    "citycountry": {"name":"اسم‌وفامیل", "status":"planned"},
    "twentyq": {"name":"بیست‌سؤالی", "status":"planned"},
    "spy": {"name":"جاسوس", "status":"planned"},
    "movie": {"name":"حدس فیلم یا آهنگ", "status":"planned"},
    "groupquiz": {"name":"مسابقه اطلاعات عمومی گروه", "status":"implemented"},
    "dice": {"name":"تاس", "status":"planned"},
    "wheel": {"name":"گردونه شانس", "status":"planned"},
    "coin": {"name":"شیر یا خط", "status":"planned"},
    "mysterybox": {"name":"جعبه شانس مجازی", "status":"planned"},
    "secretcard": {"name":"کارت مخفی", "status":"planned"},
    "luckrace": {"name":"مسابقه خوش‌شانسی", "status":"planned"},
    "typing": {"name":"تایپ سریع", "status":"planned"},
    "memory": {"name":"حافظه تصویری", "status":"planned"},
    "differences": {"name":"پیدا کردن تفاوت", "status":"planned"},
    "reaction": {"name":"واکنش سریع", "status":"planned"},
    "dailyrecord": {"name":"رکورد روزانه", "status":"planned"},
    "weeklyleague": {"name":"لیگ هفتگی", "status":"planned"},
    "dailyquest": {"name":"مأموریت روزانه", "status":"planned"},
    "pointduel": {"name":"دوئل امتیازی", "status":"planned"},
    "elimination": {"name":"مسابقه حذفی", "status":"planned"},
    "tournament": {"name":"تورنمنت گروهی", "status":"planned"},
}
GAME_CATEGORIES = {
    "اطلاعات عمومی و فکری": ["quiz","word","riddle","character","flag","math","truefalse","proverb"],
    "بازی‌های دونفره": ["tictactoe","rps","guess","wordwar","fastmath","duelword"],
    "بازی‌های گروهی": ["mafia","citycountry","twentyq","spy","movie","groupquiz"],
    "شانسی و سرگرمی": ["dice","wheel","coin","mysterybox","secretcard","luckrace"],
    "سرعت و رکورد": ["typing","memory","differences","reaction","dailyrecord"],
    "رقابت امتیازی": ["weeklyleague","dailyquest","pointduel","elimination","tournament"],
}

QUIZZES = [
    ("بزرگ‌ترین سیاره منظومه شمسی کدام است؟", ["مریخ","مشتری","زهره","عطارد"], 1),
    ("پایتخت ژاپن کدام است؟", ["سئول","پکن","توکیو","بانکوک"], 2),
    ("عدد اول بعد از ۷ کدام است؟", ["۸","۹","۱۰","۱۱"], 3),
    ("کدام جانور پستاندار است؟", ["کوسه","دلفین","تمساح","قزل‌آلا"], 1),
    ("آب در فشار معمول نزدیک چند درجه می‌جوشد؟", ["۵۰","۷۵","۱۰۰","۱۵۰"], 2),
]
_pending_quizzes = {}

def play_quiz(user):
    qid = uuid.uuid4().hex[:10]
    question, options, correct = random.choice(QUIZZES)
    _pending_quizzes[qid] = {"correct": correct, "user_id": user.id}
    return {"qid": qid, "question": question, "options": options}

def submit_quiz(user, qid, answer):
    q = _pending_quizzes.pop(qid, None)
    if not q or q["user_id"] != user.id:
        return {"message":"این سؤال منقضی شده یا متعلق به حساب دیگری است."}
    if answer == q["correct"]:
        add_result(user, 5, True)
        return {"message":"✅ پاسخ درست بود! ۵ امتیاز گرفتی."}
    add_result(user, 0, False)
    return {"message":"❌ پاسخ درست نبود؛ این دور امتیازی نگرفتی."}

def play_rps(user, choice):
    bot_choice = random.choice(["rock","paper","scissors"])
    names = {"rock":"سنگ ✊","paper":"کاغذ ✋","scissors":"قیچی ✌️"}
    wins = {("rock","scissors"),("paper","rock"),("scissors","paper")}
    if choice == bot_choice:
        add_result(user, 1, False)
        return f"🤝 مساوی شد. انتخاب ربات: {names[bot_choice]}\n۱ امتیاز مشارکت گرفتی."
    if (choice, bot_choice) in wins:
        add_result(user, 3, True)
        return f"🎉 بردی! انتخاب ربات: {names[bot_choice]}\n۳ امتیاز گرفتی."
    add_result(user, 0, False)
    return f"😅 این دور را باختی. انتخاب ربات: {names[bot_choice]}"

def play_guess(user):
    return {"number": random.randint(1,5)}

def start_group_quiz(chat_id, started_by):
    question, options, correct = random.choice(QUIZZES)
    qid = uuid.uuid4().hex[:10]
    return {"qid":qid, "chat_id":chat_id, "started_by":started_by, "question":question,
            "options":options, "correct":correct, "votes":{}, "status":"active"}

def answer_group_quiz(chat_id, user, choice, active):
    if user.id in active["votes"]:
        return {"duplicate":True, "correct":False, "finished":False}
    active["votes"][user.id] = choice
    correct = choice == active["correct"]
    if correct:
        add_result(user, 5, True)
    # This first scaffold uses a fixed short round; a production version should use a timer/job queue.
    finished = len(active["votes"]) >= 20
    return {"duplicate":False, "correct":correct, "finished":finished}
