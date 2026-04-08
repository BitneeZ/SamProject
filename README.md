# 🤖 SamProject — Голосовой ассистент с 2D-аватаром

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-В%20разработке-yellow)](#)

> 🎙️ *Интеллектуальный голосовой помощник с анимированным аватаром, распознаванием речи и генерацией ответов в реальном времени*

---

## ✨ Возможности

- 🎤 Распознавание речи — оффлайн-движок Vosk для русского языка
- 🧠 Умные ответы — интеграция с LLM для генерации текста
- 🔊 Озвучка ответов — текстовый синтез речи (TTS)
- 👾 2D-аватар — анимированный персонаж на pygame, реагирующий на речь
- ⚡ Асинхронность — многопоточная архитектура для плавной работы

---

## 🚀 Быстрый запуск

### 1. Клонирование репозитория

git clone https://github.com/BitneeZ/SamProject.git
cd SamProject

### 2. Установка зависимостей

pip install -r requirements.txt

> Если файла requirements.txt ещё нет, установите пакеты вручную:
pip install vosk pygame pillow requests

### 3. Подготовка модели и ресурсов

- Скачайте модель Vosk для русского языка:
  https://alphacephei.com/vosk/models
  Распакуйте в папку models/:
  
  SamProject/
  └── models/
      └── vosk-model-small-ru-0.22/

- Убедитесь, что в папке gifs/ есть анимации:
  - speak.gif — аватар говорит
  - not_speak.gif — аватар в режиме ожидания

### 4. Запуск проекта

python test.py

> Просто введите команду выше в терминале — и ассистент начнёт слушать вас!

---

## 📁 Структура проекта

SamProject/
├── test.py              # Точка входа: голос + аватар + AI
├── main.py              # Базовый режим без аватара
├── speech_to_text.py    # Модуль распознавания речи (Vosk)
├── nlp_dlm.py           # Генерация ответов через LLM API
├── tts.py               # Текст в речь (озвучка)
├── calibrovka.py        # Калибровка микрофона / настройки
├── vtstudio.py          # Интеграция с внешними сервисами (опционально)
├── gifs/                # Анимации аватара
│   ├── speak.gif
│   └── not_speak.gif
├── models/              # Модели Vosk
│   └── vosk-model-small-ru-0.22/
├── .gitignore
└── README.md

---

