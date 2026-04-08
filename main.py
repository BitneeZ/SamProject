from speech_to_text import LiveSpeechRecognizer
from nlp_dlm import generate_text, get_access_token
from tts import speak, stop_queue

def main():
    # Инициализируем распознаватель
    recognizer = LiveSpeechRecognizer(model_path="models/vosk-model-small-ru-0.22")

    # Цикл прослушивания
    # recognizer.listen() — это бесконечный генератор, он будет висеть здесь,
    for sentence in recognizer.listen():
        print("Вы: " + sentence)
        gen = generate_text(sentence, get_access_token())
        print("Бот: " + gen)
        speak(gen)

if __name__ == "__main__":
    main()