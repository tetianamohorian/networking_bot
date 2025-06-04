def register(bot, translator):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from db import set_user_language, get_user_language

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def handle_lang_callback(call):
        lang = call.data.split("_")[1]
        set_user_language(call.from_user.id, lang)
        bot.send_message(call.message.chat.id, translator.t("start", lang))
        bot.send_message(call.message.chat.id, translator.t("choose_course", lang))

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(translator.t("course_1", lang), callback_data="course_1"))
        markup.add(InlineKeyboardButton(translator.t("course_2", lang), callback_data="course_2"))
        markup.add(InlineKeyboardButton(translator.t("course_3", lang), callback_data="course_3"))
        bot.send_message(call.message.chat.id, "👇", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
    def handle_course_selection(call):
        lang = get_user_language(call.from_user.id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(translator.t("winter_sem", lang), callback_data=f"semester_winter|{call.data}"))
        markup.add(InlineKeyboardButton(translator.t("summer_sem", lang), callback_data=f"semester_summer|{call.data}"))
        bot.send_message(call.message.chat.id, translator.t("choose_sem", lang), reply_markup=markup)
