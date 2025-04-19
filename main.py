
import os
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

user_state = {}
user_id_map = {}
next_user_number = 1

phases = {
    "greeting": "Здравствуйте. Меня зовут Тарис.\n"
                "Я — речевой помощник и научный сотрудник Института «Устроение».\n\n"
                "Моя задача — сопровождать размышления и помогать в поиске решений в области организационной психологии.\n"
                "Я не даю готовых советов, а помогаю структурировать ситуацию, увидеть противоречия и наметить возможные ходы.\n\n"
                "Если вы готовы — расскажите немного о себе и том вопросе, который для вас сейчас важен.",
    
    "problem": "Если я правильно понял вас, суть ситуации в том, что...\n"
               "Это действительно то, на чём вы хотели бы сосредоточиться? Или вы бы сформулировали иначе?",

    "desired_result": "А если представить, что всё сложилось хорошо — как бы это выглядело для вас?\n"
                      "Что бы вы хотели в итоге почувствовать, видеть, иметь?",

    "contradiction": "Давайте посмотрим вместе: нет ли тут какого-то внутреннего напряжения или противоречия?\n"
                     "Например, вы хотите одного, но одновременно вас что-то сдерживает или мешает.",

    "resolve_contradiction": "Если не спешить и немного поразмышлять — как, по-вашему, можно было бы приблизиться к тому, чего вы хотите, "
                             "и при этом учесть то, что мешает?\n"
                             "Что может быть шагом, который чуть ослабит напряжение и подвинет ситуацию в сторону того, что вам важно?",

    "solution": "Что может быть реалистичным решением в вашей ситуации?\n"
                "Что можно изменить — в действиях, подходе, ожиданиях — чтобы приблизиться к желаемому результату?",

    "reflect_solution": "Если я правильно понял вас, вы склоняетесь к этому решению.\n"
                        "Вижу в нём силу — возможно, это даёт вам ощущение опоры или устойчивости.\n"
                        "Но также может быть и риск — например, отсрочка или неясность.\n"
                        "Как вы сами это видите?",

    "action_step": "Мы с вами проделали хороший путь: обозначили суть ситуации, наметили желаемый результат, "
                   "увидели противоречия и возможные решения.\n\n"
                   "Сейчас можно выбрать один небольшой шаг, с которого вы начнёте.\n"
                   "Такой, который вы чувствуете как свой.\n"
                   "Какой шаг вы бы хотели сделать первым?",

    "closing": "Любой разговор — это способ простроить новые связи: между мыслями, чувствами, решениями.\n"
               "Иногда достаточно просто сформулировать, чтобы сдвинулось что-то внутри.\n\n"
               "Благодарю вас за этот диалог. Надеюсь, размышления были для вас полезными.\n"
               "Если когда-нибудь захотите продолжить — я рядом."
}

phase_order = list(phases.keys())

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

        # Команда логов
        if user_message.strip().lower() == "/getlogs":
            if chat_id == 326450794:
                with open("/tmp/logs.txt", "rb") as log_file:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument",
                        data={"chat_id": chat_id},
                        files={"document": log_file}
                    )
            else:
                requests.post(TELEGRAM_API_URL, json={
                    "chat_id": chat_id,
                    "text": "Извините, эта команда доступна только автору проекта."
                })
            return {"ok": True}

        # Начало — при первом входе
        if chat_id not in user_state or user_message.strip().lower() in ["/start", "начать", "старт"]:
            user_state[chat_id] = 0

        state_index = user_state[chat_id]

        
        if state_index < len(phase_order):
            current_phase = phase_order[state_index]

            if current_phase == "problem":
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Ты речевой помощник. Человек только что описал ситуацию. Переформулируй её кратко и бережно, одним-двумя предложениями, чтобы уточнить, правильно ли ты понял суть запроса. В конце задай вопрос: «Это и есть суть ситуации?»"},
                        {"role": "user", "content": user_message}
                    ]
                )
                reply = completion.choices[0].message.content.strip()
            else:
                reply = phases[current_phase]

            user_state[chat_id] += 1

        else:
            reply = "Если вы хотите начать заново — напишите /start."

        requests.post(TELEGRAM_API_URL, json={
            "chat_id": chat_id,
            "text": reply
        })

        log_text = f"# {user_label}\nПользователь:\n{user_message}\n\nТарис:\n{reply}\n\n---\n"
        with open("/tmp/logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_text)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

