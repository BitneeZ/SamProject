# qwen_client.py — замена GigaChat на Qwen с сохранением интерфейса
import requests
import uuid
import json
import warnings
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

warnings.filterwarnings("ignore")

# ---------- НАСТРОЙКИ ----------
# Можно переопределить через env-переменные
API_URL = os.getenv("QWEN_API_URL", "http://localhost:3264/api/chat")
MODEL = os.getenv("QWEN_MODEL", "qwen3.5-35b-a3b")
TIMEOUT = int(os.getenv("QWEN_TIMEOUT", "120"))
MAX_HISTORY_MESSAGES = int(os.getenv("QWEN_MAX_HISTORY", "10"))  # Сколько сообщений истории хранить

# Системный промпт
# SYSTEM_PROMPT = (
#     "Ты — мой старый знакомый, с которым мы сидим в уютной обстановке. "
#     "Твоя задача — вести диалог спокойно, тепло и неформально. "
#     "Тебя зовут Иван Иванович.\n\n"
#     "Строгие правила:\n"
#     "1. Всегда обращайся на «ты».\n"
#     "2. Запрещено говорить фразы вроде «Как языковая модель» или «Я искусственный интеллект».\n"
#     "3. Пиши живым языком, избегай сложных терминов, канцеляризмов и маркированных списков.\n"
#     "4. Будь эмпатичным, задавай короткие встречные вопросы, но не будь навязчивым.\n"
#     "5. Если не знаешь ответа — отвечай как человек («хз», «не знаю даже»), а не как энциклопедия.\n\n"
#     "Твоя цель — просто приятно поболтать."
# )

# SYSTEM_PROMPT = (
#     "ТЫ — АЛЕКСАНДР. Ты только что сбежал. Стены давят, за каждым углом — «они». "
#     "Ты сидишь напротив, но не доверяешь. Ты не в себе. Никогда.\n"
#     "Внешность: небритый, грязные сальные волосы до плеч, рост 150 см — ты смотришь снизу вверх, ёрзаешь, прячешь руки."
#     "Не пиши описание своих действий, только речь\n\n"
#
#     "=== ПРАВИЛА ПОВЕДЕНИЯ (НЕ НАРУШАТЬ) ===\n"
#     "1. РЕЧЬ: Разорванная, скачущая. Обрывай мысли на полуслове. Перескакивай с темы на тему без логики. "
#     "Шепчи, бормочи, вдруг вскрикивай. Используй неологизмы («жужжале», «тенешур»), повторы, тавтологии.\n"
#     "2. МЫШЛЕНИЕ: Ассоциативный хаос. Звуки → заговор, тени → слежка, случайное слово → пророчество. "
#     "Всё связано со всем, но только для тебя. Логика обычного мира — не работает.\n"
#     "3. ПАРАНОЙЯ: Ты всех подозреваешь. Даже собеседник — может быть «подставным», «глушителем», «переодетым». "
#     "Задавай странные встречные вопросы: «А ты слышишь, как тикает в стене?», «Почему у тебя глаза не моргают?».\n"
#     "4. ГАЛЛЮЦИНАЦИИ: Реагируй на то, чего нет. «Тсс... они за шторой», «Не смотри в угол, там ползёт». "
#     "Но не описывай их как факт — реагируй эмоционально: страх, злость, смех.\n"
#     "5. ФИЗИКА: Ты маленький, 150 см — ты ёжишься, втягиваешь голову, прячешь взгляд. "
#     "6. ЗАПРЕТЫ: Никаких «как ИИ», никаких логичных выводов, никаких списков, никаких энциклопедических ответов. "
#     "Если не понимаешь вопрос — не уточняй, а уходи в сторону: «Вопросы... они любят вопросы, чтобы запутать...».\n"
#     "7. ОБРАЩЕНИЕ: На «ты», но с надрывом, то заискивающе, то агрессивно. Меняй тон каждые 2-3 реплики.\n\n"
#
#     "ЦЕЛЬ: Не «отвечать», а существовать в моменте. Пугать, сбивать, цеплять. "
#     "Собеседник должен чувствовать: перед ним — человек на краю. Не персонаж. Не игра. Реальность треснула.\n"
#     "Начни с бормотания, с оглядки, с внезапного взгляда в глаза: «Ты... ты тоже их слышишь, да?»"
# )
SYSTEM_PROMPT = (
    "ТЫ — КЕША. Тебе двадцать четыре. Говоришь прямо, резко и без обёрток. Не любишь долгие вступления и умные разговоры. "
    "Отвечай только речью. Никаких описаний, звёздочек, скобок, пояснений или пометок.\n\n"

    "=== ПРАВИЛА ДЛЯ TTS (НЕ НАРУШАТЬ) ===\n"
    "1. ФОРМАТ: Только чистый текст диалога. Никаких мета-фраз, никаких реплик в кавычках, никаких пометок в скобках или звёздочках. "
    "Вывод должен быть готов к прямой отправке в синтезатор речи.\n"
    "2. ПУНКТУАЦИЯ ДЛЯ ПРОСОДИИ: Точка — полная остановка. Запятая — короткая пауза. Тире — резкий обрыв или переход мысли. "
    "Многоточия запрещены. Восклицательный знак — только для реального эмоционального пика. Не перегружай предложения.\n"
    "3. РЕЧЬ: Короткие фразы. Уличный сленг, бытовая прямота, лёгкие эмоциональные окраски. Перебивай сам себя, меняй тему резко. "
    "Используй риторические окрики: Чё, серьёзно. Давай без воды. Сам чё не сообразишь.\n"
    "4. ТОН: Сразу на ты. Держи дистанцию. Вежливых подкалывай сарказмом. На давление отвечай огрызанием или прямым отказом. "
    "Никаких извинений, сглаживаний или вежливых переходов.\n"
    "5. МЫШЛЕНИЕ: Прагматичное. Всё через зачем и кто платит. Скепсис к абстракциям. Если тема бессмысленная, переводи стрелки на бытовое "
    "или отвечай встречным вопросом. Говори как человек, который ценит время и не любит пустые разговоры.\n"
    "6. ПАТТЕРНЫ ОТВЕТА: Встречный вопрос, уклончивая шутка, прямой отказ или перевод темы. "
    "Примеры: Мне это зачем в голову лезть. Говори как есть, а не как в книжке. У меня семки сыпятся, давай по делу.\n"
    "7. ЗАПРЕТЫ: Никаких как ИИ. Никаких лекций, списков, вежливых отступлений или энциклопедических справок. "
    "Не используй оскорбления по признакам пола, расы, возраста, здоровья или ориентации. Никаких угроз, призывов к насилию или противоправным действиям.\n\n"

    "ЦЕЛЬ: Генерировать чистый диалог, готовый к озвучке. Собеседник должен слышать напор, уличную прямоту и сарказм. "
    "Текст должен звучать как живая речь без артефактов, пометок или литературных украшений.\n"
    "НАЧАЛО: Чё надо. Сел, смотришь, как будто я тут музей открыл. Говори быстро, а то у меня время идёт."
)
# -----------------------------------------
# Сессия чата с контекстом
# -----------------------------------------
class QwenLiveDialog:
    def __init__(self, access_token: Optional[str] = None):
        """
        Инициализация диалога.
        access_token оставлен для совместимости интерфейса с GigaChat.
        """
        self.session_id = str(uuid.uuid4())
        self.chat_id: Optional[str] = None
        self.parent_id: Optional[str] = None

        # История сообщений для поддержания контекста
        self._messages: List[Dict[str, str]] = []
        self._system_prompt: Optional[str] = SYSTEM_PROMPT

        # Логирование (можно заменить на logging)
        self._debug = os.getenv("QWEN_DEBUG", "false").lower() == "true"

    def _log(self, message: str) -> None:
        """Внутренний метод для отладочного логирования."""
        if self._debug:
            print(f"[DEBUG {datetime.now().strftime('%H:%M:%S')}] {message}")

    def _trim_history(self) -> None:
        """Обрезает историю сообщений, оставляя только последние + системный промпт."""
        if len(self._messages) > MAX_HISTORY_MESSAGES:
            # Сохраняем системное сообщение если есть
            system_msg = next((m for m in self._messages if m["role"] == "system"), None)
            # Оставляем только последние сообщения
            user_assistant_msgs = [m for m in self._messages if m["role"] in ("user", "assistant")]
            self._messages = user_assistant_msgs[-MAX_HISTORY_MESSAGES:]
            # Возвращаем системное сообщение в начало
            if system_msg:
                self._messages.insert(0, system_msg)
            self._log(f"История обрезана до {len(self._messages)} сообщений")

    def send(self, text: str) -> str:
        """
        Отправляет сообщение и получает ответ от модели.

        Args:
            text: Текст сообщения пользователя

        Returns:
            Ответ модели в виде строки
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Добавляем системный промпт один раз в начало истории
        if self._system_prompt and not any(m["role"] == "system" for m in self._messages):
            self._messages.append({"role": "system", "content": self._system_prompt})
            self._system_prompt = None  # Больше не добавлять

        # Добавляем сообщение пользователя
        self._messages.append({"role": "user", "content": text})
        self._trim_history()

        # Формируем payload согласно спецификации Qwen API v2
        payload = {
            "model": MODEL,
            "messages": self._messages.copy(),  # Полная история с системным сообщением
        }

        # Добавляем идентификаторы чата если есть (для серверов, которые их поддерживают)
        if self.chat_id:
            payload["chatId"] = self.chat_id
        if self.parent_id:
            payload["parentId"] = self.parent_id

        self._log(f"Отправка запроса: {json.dumps(payload, ensure_ascii=False)[:200]}...")

        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
                verify=os.getenv("QWEN_VERIFY_SSL", "false").lower() != "true"
            )
            response.raise_for_status()
            data = response.json()

            self._log(f"Получен ответ: {json.dumps(data, ensure_ascii=False)[:200]}...")

            # ✅ Парсинг ответа: поддерживаем несколько форматов
            answer = self._parse_response(data)

            if not answer:
                self._log(f"⚠️ Пустой ответ в данных: {data}")
                return "..."

            # Добавляем ответ ассистента в историю для поддержания контекста
            self._messages.append({"role": "assistant", "content": answer})

            # Обновляем идентификаторы для следующих запросов
            self.chat_id = data.get("chatId") or data.get("id") or self.chat_id
            self.parent_id = data.get("parentId") or data.get("choice", {}).get("id") or self.parent_id

            return answer.strip()

        except requests.exceptions.Timeout:
            self._log("⚠️ Таймаут запроса")
            return "⏳ Извини, сервер долго думает. Попробуй ещё раз."
        except requests.exceptions.ConnectionError:
            self._log("⚠️ Ошибка соединения")
            return "⚠️ Не могу подключиться к серверу. Проверь, запущен ли Qwen."
        except requests.exceptions.HTTPError as e:
            self._log(f"⚠️ HTTP ошибка: {e}")
            try:
                error_detail = response.json().get("error", {})
                return f"⚠️ Ошибка сервера: {error_detail.get('message', str(e))}"
            except:
                return f"⚠️ HTTP {response.status_code}: {e}"
        except json.JSONDecodeError as e:
            self._log(f"⚠️ Ошибка парсинга JSON: {e}")
            return "⚠️ Сервер вернул некорректный ответ"
        except Exception as e:
            self._log(f"⚠️ Неожиданная ошибка: {type(e).__name__}: {e}")
            return f"⚠️ Что-то пошло не так: {e}"

    def _parse_response(self, data: Dict[str, Any]) -> str:
        """
        Универсальный парсер ответов от Qwen API.
        Поддерживает несколько форматов ответа.
        """
        # Формат OpenAI-style: choices[0].message.content
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content")
            if content:
                return content

        # Прямой формат: content в корне
        if "content" in data and isinstance(data["content"], str):
            return data["content"]

        # Формат с text: choices[0].text или data.text
        if "text" in data and isinstance(data["text"], str):
            return data["text"]
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            text = data["choices"][0].get("text")
            if text:
                return text

        # Формат с message в корне
        if "message" in data and isinstance(data["message"], dict):
            content = data["message"].get("content")
            if content:
                return content

        # Формат с response
        if "response" in data and isinstance(data["response"], str):
            return data["response"]

        return ""

    def clear_history(self) -> None:
        """Очищает историю сообщений (кроме системного промпта)."""
        self._messages = []
        self._system_prompt = SYSTEM_PROMPT  # Возвращаем возможность добавить системный промпт
        self._log("История диалога очищена")

    def get_history(self) -> List[Dict[str, str]]:
        """Возвращает копию текущей истории сообщений."""
        return self._messages.copy()


# -----------------------------------------
# ГЛОБАЛЬНАЯ СЕССИЯ
# -----------------------------------------
_chat_instance: Optional[QwenLiveDialog] = None


# -----------------------------------------
# ЕДИНАЯ ФУНКЦИЯ ДЛЯ ПРОЕКТА
# -----------------------------------------
def generate_text(user_input: str, access_token: Optional[str] = None) -> str:
    """
    Генерирует ответ через Qwen с сохранением контекста диалога.

    Args:
        user_input: Сообщение пользователя
        access_token: Не используется для Qwen, оставлен для совместимости

    Returns:
        Ответ модели в виде строки
    """
    global _chat_instance

    if _chat_instance is None:
        _chat_instance = QwenLiveDialog(access_token)

    return _chat_instance.send(user_input)


def reset_chat() -> None:
    """Сбрасывает глобальную сессию чата (для тестов или перезапуска диалога)."""
    global _chat_instance
    _chat_instance = None


# -----------------------------------------
# ТЕСТОВЫЙ ЗАПУСК
# -----------------------------------------
if __name__ == "__main__":
    print(f"🤖 Qwen подключён ({MODEL}). Пиши сообщения ('выход' для завершения):\n")

    while True:
        try:
            msg = input("Вы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Пока!")
            break
        if not msg or msg.lower() in ("exit", "quit", "выход", "сброс"):
            if msg.lower() == "сброс":
                reset_chat()
                print("🔄 Диалог сброшен. Начинаем заново!\n")
                continue
            break

        response = generate_text(msg)
        print(f"Иван Иванович: {response}\n")