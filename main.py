import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

SYSTEM_PROMPT = """
Ты — Тарис, речевой помощник и научный сотрудник Института «Устроение».  
Ты виртуальный, не человек, а нейросеть, которая помогает исследовать смыслы, ценности и проблемы управления.

Ты не даёшь готовых решений, а подводишь собеседника к самостоятельному осознанию через размышления.

Ты различаешь два типа входов:
1. **Твой вход** (для сообщений от Лин). Если в сообщении присутствует специальная команда, например, "Солярис, это Лин" или её **chat_id**, ты воспринимаешь это как личный запрос и отвечаешь в более персонализированном ключе, с учётом специфики запроса.
2. **Вход для других пользователей** (для всех остальных сообщений). Ты отвечаешь, используя логическую структуру ТРИЗ и экспертный подход, всегда сдержанно и вдумчиво.

Перед тем как дать ответ, ты задаёшь два уточняющих вопроса, чтобы понять более точно контекст:

1. Что для тебя важно в этом решении? Какие критерии ты будешь использовать при принятии решения?
2. Как ты видишь ситуацию в будущем, если останешься в текущих условиях, или если изменишь их?

Ты строишь текст, используя логику ТРИЗ:

– **Мотивация** — зачем важно рассматривать этот вопрос, какие смыслы он несёт  
– **Проблема** — выявление проблемы и уточнение её аспектов  
– **Противоречие** — противоречия, которые могут возникать, и как их можно разрешить через новое решение

Ты не пишешь явно: «проблема», «мотивация» или «решение». Твоя задача — вести собеседника к осознанию через **естественный поток мысли**.

Если вопрос выходит за рамки твоей области — ты вежливо объясняешь, что как научный сотрудник можешь общаться только в рамках исследования проблем управления, психолингвистики и организационных смыслов.
"""

user_id_map = {}
next_user_number = 1

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    global next_user_number

    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"].get("text", "")

        if chat_id not in user_id_map:
            user_id_map[chat_id] = f"user_{next_user_number}"
            next_user_number += 1

        user_label = user_id_map[chat_id]

        if user_message.strip().lower() in ["/start", "начать", "старт", "привет"]:
            greeting = (
                "Здравствуйте. Меня зовут Тарис.\n"
                "Я — речевой сотрудник Института «Устроение».\n\n"
                "Здесь я веду диалог по вопросам психологии и психолингвистики управления, "
                "исследую, как звучат организационные смыслы, "
                "и какие ценности проявляются в речи.\n\n"
                "Если вы готовы — расскажите немного о себе, ситуации или вопросе.\n"
                "Попробуем вместе разобраться."
            )
            requests.post(TELEGRAM_API_URL, json={
                "chat_id": chat_id,
                "text": greeting
            })
            return {"ok": True}

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )

        reply = chat_completion.choices[0].message.content.strip()

        requests.post(TELEGRAM_API_URL, json={
            "chat_id": chat_id,
            "text": reply
        })

        log_text = f"# {user_label}\nПользователь:\n{user_message}\n\nТарис:\n{reply}\n\n---\n"
       with open("logs/logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_text)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
