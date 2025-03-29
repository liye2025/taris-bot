import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

# Настройки
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

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"].get("text", "")

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

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
