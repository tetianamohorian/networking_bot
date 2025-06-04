def register(bot, translator):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from db import get_user_language

    @bot.callback_query_handler(func=lambda call: call.data.startswith("subject|"))
    def handle_subject_options(call):
        lang = get_user_language(call.from_user.id)
        subject = call.data.split("|", 1)[1]
        options = translator.get_subject_options(subject)

        markup = InlineKeyboardMarkup(row_width=1)
        for opt in options:
            text = translator.t(opt, lang)
            markup.add(InlineKeyboardButton(text, callback_data=f"action|{subject}|{opt}"))

        bot.send_message(call.message.chat.id, f"📘 {subject}", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("subject_id|"))
    def handle_subject_id(call):
        lang = get_user_language(call.from_user.id)
        index = call.data.split("|")[1]
        subject = translator.subject_cache.get(index)

        if not subject:
            bot.send_message(call.message.chat.id, "⚠️ Predmet nebol nájdený.")
            return

        options = translator.get_subject_options(subject)
        markup = InlineKeyboardMarkup(row_width=1)
        for opt in options:
            text = translator.t(opt, lang)
            markup.add(InlineKeyboardButton(text, callback_data=f"action|{subject}|{opt}"))


        bot.send_message(call.message.chat.id, f"📘 {subject}", reply_markup=markup)



