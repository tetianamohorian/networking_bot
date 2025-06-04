# handlers/executor_handler.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from request_manager import mark_request_as_taken, get_request, mark_request_as_done
from db import get_user_language

user_states = {}

import yaml

with open("data/subjects.yaml", "r", encoding="utf-8") as f:
    subject_map = yaml.safe_load(f)

def resolve_pretty_names(subject_key: str, action_key: str, subject_map: dict):
    for pretty_subject, action_list in subject_map.items():
        normalized_key = pretty_subject.replace(" ", "_")
        if normalized_key.lower() == subject_key.lower():
            return pretty_subject, action_key
    return subject_key, action_key

def register(bot, translator):
   @bot.callback_query_handler(func=lambda call: call.data.startswith("accept|"))
   def handle_accept(call):
        req_id = call.data.split("|", 1)[1]
        user = call.from_user
        lang = get_user_language(user.id)

        # передаём объект user, не строку
        success, requester_id, original_message_id, group_chat_id = mark_request_as_taken(req_id, user)

        if not success:
            bot.answer_callback_query(call.id, translator.t("accept_fail", lang))
            return

        bot.answer_callback_query(call.id, translator.t("accept_success", lang))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        request = get_request(req_id)

        # распаковываем все значения (12 полей включая taken_by_id)
        username     = request["requester_username"]
        subject_key  = request["subject"]
        action_key   = request["action"]
        deadline     = request["deadline"]
        details      = request["details"]



        subject, action = resolve_pretty_names(subject_key, action_key, subject_map)

        user_states[user.id] = {
            "assigned_request_id": req_id,
            "recipient_id": requester_id,
            "original_message_id": original_message_id,
            "group_chat_id": group_chat_id,
            "action": action_key,
        }

        
        bot.send_message(user.id, translator.t("assigned", lang).format(req_id=req_id))

        formatted_card = (
            f"{translator.t('from', lang)} @{username}\n"
            f"{translator.t('subject', lang)} {subject}\n"
            f"{translator.t('type', lang)} {translator.t(action, lang)}\n"
            f"{translator.t('deadline', lang)} {deadline}\n"
            f"{translator.t('details', lang)} {details}"
        )

        bot.send_message(
            user.id,
            f"{translator.t('task_card', lang).format(req_id=req_id)}\n\n{formatted_card}",
            parse_mode="HTML"
        )

        if action_key == "tutoring":
            bot.send_message(
                user.id,
                translator.t("tutoring_link_prompt", lang),
                reply_markup=ForceReply(selective=False)
            )
            user_states[user.id]["step"] = "tutoring_link"
        else:
            bot.send_message(
                user.id,
                translator.t("upload_solution", lang),
                reply_markup=ForceReply(selective=False)
            )
            user_states[user.id]["step"] = "awaiting_delivery"

        
        bot.send_message(requester_id, translator.t("user_notified", lang).format(req_id=req_id))


   @bot.message_handler(content_types=["text", "photo", "document"], func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "awaiting_delivery")
   def handle_step_1(message):
        lang = get_user_language(message.from_user.id)
        state = user_states.get(message.from_user.id, {})
        action = state.get("action")
        state["responses"] = {}
        user_states[message.from_user.id] = state

        if action == "tutoring":
            bot.send_message(message.chat.id, translator.t("tutoring_link_prompt", lang))
            state["step"] = "tutoring_link"
        else:
            if message.content_type in ["photo", "document"]:
                state["file"] = message
                msg = bot.send_message(message.chat.id, translator.t("price_prompt", lang))
                bot.send_message(
                    message.chat.id,
                    translator.t("send_price", lang),
                    reply_markup=ForceReply(selective=False),
                    reply_to_message_id=msg.message_id
                )
                state["step"] = "written_price"
            else:
                bot.send_message(message.chat.id, translator.t("please_upload", lang))
                state["step"] = "awaiting_delivery"

   @bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "tutoring_link")
   def handle_tutoring_link(message):
        lang = get_user_language(message.from_user.id)
        state = user_states[message.from_user.id]
        if "responses" not in state:
            state["responses"] = {}
        state["responses"]["link"] = message.text
        state["step"] = "tutoring_time"

        msg = bot.send_message(message.chat.id, translator.t("tutoring_time_prompt", lang))
        bot.send_message(
            message.chat.id,
            translator.t("send_time", lang),
            reply_markup=ForceReply(selective=False),
            reply_to_message_id=msg.message_id
        )

   @bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "tutoring_time")
   def handle_tutoring_time(message):
        lang = get_user_language(message.from_user.id)
        state = user_states[message.from_user.id]
        state["responses"]["time"] = message.text
        state["step"] = "tutoring_price"

        msg = bot.send_message(message.chat.id, translator.t("tutoring_price_prompt", lang))
        bot.send_message(
            message.chat.id,
            translator.t("send_price", lang),
            reply_markup=ForceReply(selective=False),
            reply_to_message_id=msg.message_id
        )

   @bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("step") == "tutoring_price")
   def handle_tutoring_price(message):
        lang = get_user_language(message.from_user.id)
        state = user_states[message.from_user.id]
        price = message.text.strip()
        if "€" not in price:
            price += " €/hod"

        state["responses"]["price"] = price
        state["step"] = "tutoring_iban"

        msg = bot.send_message(message.chat.id, translator.t("iban_prompt", lang))
        bot.send_message(
            message.chat.id,
            translator.t("send_iban", lang),
            reply_markup=ForceReply(selective=False),
            reply_to_message_id=msg.message_id
        )

   @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "tutoring_iban")
   def finalize_tutoring(message):
        lang = get_user_language(message.from_user.id)
        state = user_states.pop(message.from_user.id)
        req_id = state["assigned_request_id"]
        recipient_id = state["recipient_id"]
        group_chat_id = state["group_chat_id"]
        original_message_id = state["original_message_id"]
        responses = state["responses"]
        responses["iban"] = message.text
        username = message.from_user.username or f"ID {message.from_user.id}"

        msg = translator.t("tutoring_summary", lang).format(
            req_id=req_id,
            link=responses["link"],
            time=responses["time"],
            price=responses["price"],
            iban=responses["iban"]
        )
        bot.send_message(recipient_id, msg)

        closure_note = translator.t("closed_by", lang).format(req_id=req_id, username=username)
        try:
            bot.send_message(group_chat_id, closure_note, reply_to_message_id=original_message_id)
        except Exception as e:
            if "message to be replied not found" in str(e):
                bot.send_message(group_chat_id, closure_note)

        mark_request_as_done(req_id, bot, translator)
        try:
            bot.edit_message_reply_markup(group_chat_id, original_message_id, reply_markup=None)
        except Exception:
            pass

   @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "written_price")
   def handle_written_price(message):
        lang = get_user_language(message.from_user.id)
        state = user_states[message.from_user.id]
        price = message.text.strip()
        if "€" not in price:
            price += " €"
        state["responses"] = {"price": price}
        user_states[message.from_user.id] = state

        prompt = bot.send_message(message.chat.id, translator.t("iban_prompt", lang))
        bot.send_message(
            message.chat.id,
            translator.t("send_iban", lang),
            reply_markup=ForceReply(selective=False),
            reply_to_message_id=prompt.message_id
        )

        state["step"] = "written_iban"

   @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "written_iban")
   def finalize_written(message):
        lang = get_user_language(message.from_user.id)
        state = user_states.pop(message.from_user.id)
        file_message = state.get("file")
        req_id = state["assigned_request_id"]
        recipient_id = state["recipient_id"]
        group_chat_id = state["group_chat_id"]
        original_message_id = state["original_message_id"]
        responses = state["responses"]
        responses["iban"] = message.text
        username = message.from_user.username or f"ID {message.from_user.id}"

        caption = f"💵 {translator.t('price', lang)}: {responses['price']}\n🏦 {translator.t('iban', lang)}: {responses['iban']}"
        if file_message.content_type == "photo":
            bot.send_photo(recipient_id, file_message.photo[-1].file_id, caption=caption)
        elif file_message.content_type == "document":
            bot.send_document(recipient_id, file_message.document.file_id, caption=caption)

        closure_note = translator.t("closed_by", lang).format(req_id=req_id, username=username)
        try:
            bot.send_message(group_chat_id, closure_note, reply_to_message_id=original_message_id)
        except Exception as e:
            if "message to be replied not found" in str(e):
                bot.send_message(group_chat_id, closure_note)

        mark_request_as_done(req_id, bot, translator)
        try:
            bot.edit_message_reply_markup(group_chat_id, original_message_id, reply_markup=None)
        except Exception:
            pass
