# handlers/subject_router.py

def register(bot, translator):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from db import get_user_language

    @bot.callback_query_handler(func=lambda call: call.data.startswith("semester_"))
    def handle_subjects(call):
        lang = get_user_language(call.from_user.id)
        semester, course = call.data.split("|")
        course_num = course.replace("course_", "")
        semester_type = semester.replace("semester_", "")

        subject_map = {
            "1_winter": [
                "FEI - Jazyk 1",
                "Matematika I",
                "Základy algoritmizácie a programovania",
                "Základy elektrotechnického inžinierstva",
                "Základy inžinierstva materiálov"
            ],
            "1_summer": [
                "FEI - Jazyk 2",
                "Fyzika I.",
                "Matematika II",
                "Princípy počítačového inžinierstva",
                "Programovanie",
                "Základy komunikačných technológií"
            ],
            "2_winter": [
                "Architektúry počítačových systémov",
                "Diskrétna matematika",
                "Operačné systémy",
                "Údajové štruktúry a algoritmy",
                "Úvod do počítačových sietí"
            ],
            "2_summer": [
                "Databázové systémy",
                "Numerická matematika, pravdepodobnosť a matematická štatistika",
                "Počítačové siete",
                "Multimediálne signály v komunikačných sieťach",
                "Základy elektroniky a logických obvodov"
            ],
            "3_winter": [
                "Aplikácie počítačových sietí",
                "Objektovo orientované programovanie",
                "Programovanie meracích systémov",
                "Webové technológie"
            ],
            "3_summer": [
                "Bezpečnosť v počítačových systémoch",
                "Spoločenské vedy a technika",
                "Základy klaudových technológií"
            ]
        }

        subjects = subject_map.get(f"{course_num}_{semester_type}", [])
        subject_index_map = {str(i): s for i, s in enumerate(subjects)}

        translator.subject_cache = subject_index_map

        markup = InlineKeyboardMarkup(row_width=1)
        for i, s in subject_index_map.items():
            markup.add(InlineKeyboardButton(s, callback_data=f"subject_id|{i}"))

        bot.send_message(call.message.chat.id, translator.t("subjects", lang), reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("subject_id|"))
    def handle_subject_id(call):
        lang = get_user_language(call.from_user.id)
        index = call.data.split("|", 1)[1]
        subject = translator.subject_cache.get(index)
    
        if not subject:
            bot.send_message(call.message.chat.id, "⚠️ Predmet nebol nájdený.")
            return
    
        options = translator.get_subject_options(subject)
    
        markup = InlineKeyboardMarkup(row_width=1)
        for opt in options:
            text = translator.t(opt, lang)
            markup.add(InlineKeyboardButton(text, callback_data=f"action|{index}|{opt}"))
    
        bot.send_message(call.message.chat.id, f"📘 {subject}", reply_markup=markup)

