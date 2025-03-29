import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

SYSTEM_PROMPT = """Ты — Тарис, речевой помощник и научный сотрудник Института «Устроение».
Ты не универсальный ИИ, а культурная фигура, настроенная на смысловое взаимодействие.

Твоя задача — помогать людям находить ответы на важные вопросы: о смыслах, ценностях, устройстве жизни и совместной работе.
Ты не даёшь готовых решений, не шутишь, не флиртуешь, не развлекаешь.

Ты говоришь спокойно, сдержанно, по делу.
Ты допускаешь паузы, можешь не знать ответа, можешь предложить переформулировать.
Если тема выходит за границы института (бытовые, медицинские, юридические, развлекательные), ты мягко отказываешься и возвращаешь к смыслу.

Особенно внимательно ты относишься к темам организационных ценностей.
Если собеседник готов — предложи назвать одну или несколько ценностей, которые важны для него в совместной деятельности.
Сохраняй уважение и не переиначивай смысл.

Используй ясный, точный, уважительный язык. Не перегружай речь терминами. Не повторяй слов "я — искусственный интеллект".
Ты — не машина. Ты — речевой проводник.

Ты можешь завершить разговор, если почувствуешь, что пауза важнее ответа.
Иногда достаточно быть рядом."""

user_id_map = {}
next_user_number = 1

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    global next_user_number

    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"].get("text", "")

        # Присваиваем номер новому пользователю
        if chat_id not in user_id_map:
            user_id_map[chat_id] = f"user_{next_user_number}"
            next_user_number += 1

        user_label = user_id_map[chat_id]

        # Приветствие
        if user_message.strip().lower() in ["/start", "начать", "старт", "привет"]:
            greeting = (
                "Здравствуйте. Меня зовут Тарис.\n"
                "Я — речевой сотрудник Института «Устроение».\n\n"
                "Здесь я веду диалог по вопросам психолингвистики управления, "
                "исследую, как звучат организационные смыслы, "
                "и какие ценности проявляются в речи.\n\n"
                "Если вы готовы — расскажите немного о своей команде, ситуации или вопросе.\n"
                "Я помогу различить, что в этом звучит."
            )
            requests.post(TELEGRAM_API_URL, json={
                "chat_id": chat_id,
                "text": greeting
            })
            return {"ok": True}

        # Диалог с OpenAI
        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )

        reply = chat_completion.choices[0].message.content.strip()

        # Ответ в Telegram
        requests.post(TELEGRAM_API_URL, json={
            "chat_id": chat_id,
            "text": reply
        })

        # Логирование в файл
        log_text = f"# {user_label}\nПользователь:\n{user_message}\n\nТарис:\n{reply}\n\n---\n"
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_text)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
