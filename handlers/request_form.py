from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from db import get_user_language
from request_manager import save_request, format_request_card, TEAM_CHAT_ID
import yaml

user_states = {}

with open("data/subjects.yaml", "r", encoding="utf-8") as f:
    subject_map = yaml.safe_load(f)

def register(bot, translator):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("action|"))
    def ask_deadline(call):
        _, subject, action = call.data.split("|", 2)
        lang = get_user_language(call.from_user.id)

        user_states[call.from_user.id] = {
            "subject": subject,
            "action": action,
            "step": "ask_deadline"
        }
        bot.send_message(call.message.chat.id, translator.t("ask_deadline", lang), reply_markup=ForceReply(selective=False))

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "ask_deadline")
    def handle_deadline(message):
        state = user_states[message.from_user.id]
        state["deadline"] = message.text
        state["step"] = "ask_details"
        lang = get_user_language(message.from_user.id)
        bot.send_message(message.chat.id, translator.t("ask_details", lang), reply_markup=ForceReply(selective=False))

    @bot.message_handler(content_types=["text", "photo", "document"], func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "ask_details")
    def finalize_request(message):
        state = user_states.pop(message.from_user.id, {})
        if not state:
            return
    
        subject_key = state["subject"]
        subject = translator.subject_cache.get(subject_key, subject_key)
        action = state["action"]
        deadline = state["deadline"]
        user_id = message.from_user.id
        username = message.from_user.username or "(no username)"
        lang = get_user_language(user_id)
    
       
        details = message.caption if message.content_type in ["photo", "document"] else message.text
    
        
        temp_card = format_request_card("-", username, subject, action, deadline, details, translator, lang)
    
        
        accept_btn = InlineKeyboardMarkup()
        accept_btn.add(InlineKeyboardButton(translator.t("accept_button", lang), callback_data="accept|pending"))
    
       
        delivery_type = message.content_type
    
        
        if delivery_type == "photo":
            sent = bot.send_photo(TEAM_CHAT_ID, message.photo[-1].file_id, caption=temp_card, parse_mode="HTML", reply_markup=accept_btn)
        elif delivery_type == "document":
            sent = bot.send_document(TEAM_CHAT_ID, message.document.file_id, caption=temp_card, parse_mode="HTML", reply_markup=accept_btn)
        else:
            sent = bot.send_message(TEAM_CHAT_ID, temp_card, parse_mode="HTML", reply_markup=accept_btn)
    
        
        req_id = save_request(user_id, username, subject, action, deadline, details, sent.message_id)
    
        
        final_card = format_request_card(req_id, username, subject, action, deadline, details, translator, lang)
        final_btn = InlineKeyboardMarkup()
        final_btn.add(InlineKeyboardButton(translator.t("accept_button", lang), callback_data=f"accept|{req_id}"))
    
        
        try:
            if delivery_type == "photo" or delivery_type == "document":
                bot.edit_message_caption(chat_id=TEAM_CHAT_ID, message_id=sent.message_id, caption=final_card, parse_mode="HTML", reply_markup=final_btn)
            else:
                bot.edit_message_text(chat_id=TEAM_CHAT_ID, message_id=sent.message_id, text=final_card, parse_mode="HTML", reply_markup=final_btn)
        except Exception as e:
            print(f"⚠️ Не удалось обновить сообщение: {e}")
    
        
        bot.send_message(message.chat.id, translator.t("confirmation_sent", lang))
    
    
    