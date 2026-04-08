# import base64
# import requests
# import json
# import warnings

# warnings.filterwarnings("ignore")

# # Загрузка ключей
# try:
#     with open("keys.json", 'r', encoding='utf-8') as f:
#         secrets = json.load(f)
#     GIGACHAT_CLIENT_ID = secrets.get("gigachat_client_id")
#     GIGACHAT_SECRET = secrets.get("gigachat_secret")
#     GIGACHAT_SCOPE = secrets.get("gigachat_scope")
# except FileNotFoundError:
#     print("Ошибка: файл keys.json не найден.")
#     # Можно задать заглушки или выйти, если критично

# def get_access_token():
#     url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
#     auth_string = f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_SECRET}"
#     auth_key = base64.b64encode(auth_string.encode()).decode()

#     payload = {"scope": GIGACHAT_SCOPE}
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "Accept": "application/json",
#         "RqUID": "096c79fd-9c28-40a9-9c5f-ee00ead9c348",
#         "Authorization": f"Basic {auth_key}"
#     }

#     response = requests.post(url, headers=headers, data=payload, verify=False)
    
#     if response.status_code != 200:
#         raise Exception("Ошибка получения токена: " + response.text)

#     return response.json()["access_token"]

# # --- ИСТОРИЯ ДИАЛОГА (Глобальная переменная) ---
# # Она инициализируется один раз при импорте модуля
# conversation_history = [
#     {
#         "role": "system",
#         "content": (
#             "Ты — мой старый знакомый, с которым мы сидим в уютной обстановке. "
#             "Твоя задача — вести диалог спокойно, тепло и неформально.\n\n"
#             "Строгие правила:\n"
#             "1. Всегда обращайся на «ты».\n"
#             "2. Запрещено говорить фразы вроде «Как языковая модель» или «Я искусственный интеллект».\n"
#             "3. Пиши живым языком, избегай сложных терминов, канцеляризмов и маркированных списков.\n"
#             "4. Будь эмпатичным, задавай короткие встречные вопросы, но не будь навязчивым.\n"
#             "5. Если не знаешь ответа — отвечай как человек («хз», «не знаю даже»), а не как энциклопедия.\n\n"
#             "Твоя цель — просто приятно поболтать."
#         )
#     }
# ]

# # Добавил history=None, чтобы аргумент стал необязательным
# def generate_text(user_input: str, access_token: str, history: list = None):
#     url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

#     headers = {
#         "Accept": "application/json",
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     }

#     # Если история не передана извне, используем глобальную переменную этого модуля
#     if history is None:
#         history = conversation_history

#     # 1. Добавляем сообщение пользователя в историю
#     history.append({
#         "role": "user",
#         "content": user_input
#     })

#     # Формируем тело запроса
#     data = {
#         "model": "GigaChat",
#         "messages": history, 
#         "max_tokens": 1500,
#         "temperature": 1.1
#     }

#     try:
#         response = requests.post(url, headers=headers, json=data, verify=False)
#         response.raise_for_status()
        
#         result_content = response.json()["choices"][0]["message"]["content"]

#         # 2. Добавляем ответ модели в историю
#         history.append({
#             "role": "assistant",
#             "content": result_content
#         })

#         return result_content

#     except Exception as e:
#         # Если произошла ошибка, лучше удалить последнее сообщение пользователя,
#         # чтобы не сломать контекст "висящим" вопросом без ответа.
#         if history and history[-1]["role"] == "user":
#             history.pop()
#         return f"Произошла ошибка: {e}"

# # Тестовый блок (запускается только если запустить этот файл напрямую)
# if __name__ == "__main__":

#     token = get_access_token()
#     print("--- Чат начат (введите 'выход' для завершения) ---")
#     while True:
#         event = input("Вы: ")
#         if event.lower() in ["выход", "exit"]:
#             break
        
#         # Здесь history не передаем, функция сама возьмет global conversation_history
#         text = generate_text(event, token) 
#         print(f"Бот: {text}")
import requests
import base64
import uuid
import json
import warnings

warnings.filterwarnings("ignore")

# ---------- LOAD SECRETS ----------
with open("keys.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

GIGACHAT_CLIENT_ID = secrets.get("gigachat_client_id")
GIGACHAT_SECRET = secrets.get("gigachat_secret")
GIGACHAT_SCOPE = secrets.get("gigachat_scope")


# -----------------------------------------
# Получение access_token (НЕ МЕНЯЕМ)
# -----------------------------------------
def get_access_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    auth_string = f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_SECRET}"
    auth_key = base64.b64encode(auth_string.encode()).decode()

    payload = {"scope": GIGACHAT_SCOPE}

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": "7e5dcc3e-a1eb-4c2f-b145-f6fcfc050eed",
        "Authorization": f"Basic {auth_key}"
    }

    response = requests.post(
        url,
        headers=headers,
        data=payload,
        verify=False
    )

    if response.status_code != 200:
        raise Exception("Ошибка получения токена: " + response.text)

    return response.json()["access_token"]

# -----------------------------------------
# Сессия чата с историей (НЕ МЕНЯЕМ ЛОГИКУ)
# -----------------------------------------
class GigaChatLiveDialog:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session_id = str(uuid.uuid4())

        self.messages = [
            {
                "role": "system",
                "content": (
                    "Ты — мой старый знакомый, с которым мы сидим в уютной обстановке. "
            "Твоя задача — вести диалог спокойно, тепло и неформально.\n\n"
            "Строгие правила:\n"
            "1. Всегда обращайся на «ты».\n"
            "2. Запрещено говорить фразы вроде «Как языковая модель» или «Я искусственный интеллект».\n"
            "3. Пиши живым языком, избегай сложных терминов, канцеляризмов и маркированных списков.\n"
            "4. Будь эмпатичным, задавай короткие встречные вопросы, но не будь навязчивым.\n"
            "5. Если не знаешь ответа — отвечай как человек («хз», «не знаю даже»), а не как энциклопедия.\n\n"
            "Твоя цель — просто приятно поболтать."
                )
            }
        ]

    def send(self, text: str) -> str:
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Session-ID": self.session_id
        }

        self.messages.append({
            "role": "user",
            "content": text
        })

        payload = {
            "model": "GigaChat",
            "messages": self.messages,
            "temperature": 1.0,
            "max_tokens": 150
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False
        )

        if response.status_code != 200:
            raise Exception("Ошибка GigaChat: " + response.text)

        answer = response.json()["choices"][0]["message"]["content"]

        self.messages.append({
            "role": "assistant",
            "content": answer
        })

        return answer


# -----------------------------------------
# ГЛОБАЛЬНАЯ ЖИВАЯ СЕССИЯ
# -----------------------------------------
_chat_instance: GigaChatLiveDialog | None = None


# -----------------------------------------
# ЕДИНАЯ ФУНКЦИЯ ДЛЯ ПРОЕКТА
# -----------------------------------------
def generate_text(user_input: str, access_token: str) -> str:
    global _chat_instance

    if _chat_instance is None:
        _chat_instance = GigaChatLiveDialog(access_token)

    return _chat_instance.send(user_input)
         