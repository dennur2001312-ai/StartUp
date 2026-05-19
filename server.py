import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
# Разрешаем CORS, чтобы твой Mini App на Vercel мог спокойно слать запросы сюда на Render
CORS(app, resources={r"/api/chat": {"origins": "*"}})

# =====================================================================
# НАСТРОЙКА КЛИЕНТА AITUNNEL
# Вставь сюда свой реальный API-ключ от личного кабинета AITUNNEL
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
        model_type = data.get('model', 'gemini')  # Прилетает из HTML: gemini, chatgpt, deepseek, qwen
        system_prompt = data.get('prompt', 'Ты полезный, умный и креативный ассистент.')
        history = data.get('history', [])  # История сообщений для памяти бота

        # Сопоставляем внутренние имена моделей из HTML с официальными ID моделей в AITUNNEL
        # (Если имена моделей в AITUNNEL изменятся, просто поправь правые значения)
        model_mapping = {
            "gemini": "gemini-2.5-flash-lite",         
            "chatgpt": "gpt-4o-mini",       
            "deepseek": "deepseek-chat",    
            "qwen": "qwen3.5-9b"              
        }
        
        target_model = model_mapping.get(model_type, model_type)

        # Формируем список сообщений для API по стандарту OpenAI
        api_messages = []
        
        # 1. Добавляем системную инструкцию
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
            
        # 2. Переносим историю диалога для сохранения контекста
        for msg in history:
            role = "user" if msg.get("sender") == "user" else "assistant"
            api_messages.append({"role": role, "content": msg.get("text", "")})
            
        # 3. Добавляем последнее сообщение пользователя
        if user_text:
            api_messages.append({"role": "user", "content": user_text})

        # Отправляем запрос в туннель
        response = client.chat.completions.create(
            model=target_model,
            messages=api_messages,
            temperature=0.7
        )

        # Забираем текстовый ответ нейросети
        ai_reply = response.choices[0].message.content

        return jsonify({
            "success": True,
            "reply": ai_reply
        })

    except Exception as e:
        # В случае ошибки (например, кончился баланс в AITUNNEL) возвращаем красивый текст ошибки
        return jsonify({
            "success": False,
            "reply": f"Ошибка на стороне бэкенда/AITUNNEL: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Обязательно слушаем порт, который выдаст Render (по умолчанию 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
