import torch
import sounddevice as sd
import time
import threading

# Загрузка модели (как в твоем примере)
local_file = 'models/tts_model.pt' 
device = torch.device('cpu')
# Если файл уже есть локально:
model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

# Флаг для контроля остановки (потокобезопасное событие)
stop_event = threading.Event()

def speak(text):
    """
    Функция, которая будет выполняться в отдельном потоке.
    Она генерирует и воспроизводит звук.
    """

    sample_rate = 48000
    speaker = 'aidar'

    # Если нажал стоп до начала генерации - выходим
    if stop_event.is_set():
        return

    # Генерация аудио
    audio = model.apply_tts(text=text,
                            speaker=speaker,
                            sample_rate=sample_rate)

    if stop_event.is_set():
        return

    # Воспроизведение
    sd.play(audio, sample_rate)
    
    # Ждем окончания, но с возможностью прерывания
    # sd.wait() блокирует наглухо, поэтому мы используем цикл проверки
    while sd.get_stream().active:
        if stop_event.is_set():
            sd.stop()  # Резко останавливаем звук
            break
        time.sleep(0.1)

def stop_queue(sentence):

    # Список стоп-слов
    stop_words = ["стоп", "хватит", "заткнись", "тихо"]

    while True:

        user_input = sentence.strip()
        
        if not user_input:
            continue

        # Проверка на стоп-слова
        if user_input.lower() in stop_words:
            stop_event.set() # Сигнализируем потоку остановиться
            sd.stop()        # Принудительно глушим звук
            continue

        # Если это обычный текст
        stop_event.clear() # Сбрасываем флаг остановки перед новым запуском
        
        # Запускаем синтез в отдельном потоке, чтобы input() не блокировался
        t = threading.Thread(target=speak, args=(user_input,))
        t.start()

if __name__ == "__main__":
    stop_queue()