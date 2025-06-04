def register(bot, translator):
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(translator.t("lang_uk", "sk"), callback_data="lang_uk"))
        markup.add(
            InlineKeyboardButton(translator.t("lang_ru", "sk"), callback_data="lang_ru"))
        markup.add(
            InlineKeyboardButton(translator.t("lang_sk", "sk"), callback_data="lang_sk"))
        markup.add(
            InlineKeyboardButton(translator.t("lang_en", "sk"), callback_data="lang_en"))
        bot.send_message(message.chat.id, translator.t("choose_lang", "sk"), reply_markup=markup)
        
