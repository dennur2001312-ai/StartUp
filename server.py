import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Обход ошибки "unexpected keyword argument 'proxies'" на хостинге Render
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

app = Flask(__name__)
# Разрешаем CORS, чтобы Mini App на Vercel мог слать запросы на этот сервер
CORS(app, resources={r"/api/chat": {"origins": "*"}})

# =====================================================================
# НАСТРОЙКА КЛИЕНТА AITUNNEL
# Вставь сюда свой токен из личного кабинета AITUNNEL
AITUNNEL_API_KEY = "sk-aitunnel-PnpihZDAxlnnlC5DHuWI9EpS1u5SCHIv"
AITUNNEL_BASE_URL = "https://api.aitunnel.ru/v1" 

client = OpenAI(
    api_key=AITUNNEL_API_KEY,
    base_url=AITUNNEL_BASE_URL
)
# =====================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "reply": "Получен пустой запрос"}), 400
        
        user_text = data.get('text', '')
        model_type = data.get('model', 'gemini')  # Прилетает из твоего HTML
        system_prompt = data.get('prompt', 'Ты полезный, умный и креативный ассистент.')
        history = data.get('history', [])  # Контекст общения

        # Связываем кнопки из твоего HTML с официальными ID моделей в AITUNNEL
        model_mapping = {
            "gemini": "gemini-2.5-flash-lite",         
            "chatgpt": "gpt-4o-mini",       
            "deepseek": "deepseek-chat",    
            "qwen": "qwen3.5-9b"              
        }
        
        target_model = model_mapping.get(model_type, model_type)

        # Собираем массив сообщений по стандарту OpenAI API
        api_messages = []
        
        # 1. Системный промпт (инструкция)
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
            
        # 2. Подгружаем историю диалога, чтобы бот всё помнил
        for msg in history:
            role = "user" if msg.get("sender") == "user" else "assistant"
            api_messages.append({"role": role, "content": msg.get("text", "")})
            
        # 3. Новое сообщение от пользователя
        if user_text:
            api_messages.append({"role": "user", "content": user_text})

        # Отправка запроса в AITUNNEL
        response = client.chat.completions.create(
            model=target_model,
            messages=api_messages,
            temperature=0.7
        )

        # Вытаскиваем чистый текст ответа нейросети
        ai_reply = response.choices[0].message.content

        return jsonify({
            "success": True,
            "reply": ai_reply
        })

    except Exception as e:
        # Если что-то пойдёт не так, сайт выведет понятную ошибку вместо падения
        return jsonify({
            "success": False,
            "reply": f"Ошибка бэкенда или AITUNNEL: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Render сам передает порт в переменные окружения, Flask его подхватит
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
