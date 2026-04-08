import queue
import sys
import json
import pyaudio
from vosk import Model, KaldiRecognizer

class LiveSpeechRecognizer:
    def __init__(self, model_path="model", device_index=None):
        """
        model_path: путь к папке с распакованной моделью Vosk.
        device_index: индекс микрофона (None для дефолтного).
        """
        self.model_path = model_path
        self.device_index = device_index
        self.rate = 16000 # Частота дискретизации, стандарт для Vosk
        self.chunk_size = 8000 # Размер буфера
        self.is_running = False
        
        # Очередь для передачи аудиоданных между потоками (если нужно)
        # В данном простом варианте читаем напрямую.
        
        try:
            self.model = Model(self.model_path)
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            print("Убедитесь, что папка 'model' находится рядом со скриптом.")
            sys.exit(1)

    def listen(self):
        """
        Генератор, который возвращает распознанный текст в реальном времени.
        """
        # Настройка PyAudio
        p = pyaudio.PyAudio()
        

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk_size,
                        input_device_index=self.device_index)
        
        rec = KaldiRecognizer(self.model, self.rate)
        self.is_running = True
        
        print("Голосовой ввод активирован. Говорите...")
        
        while self.is_running:
            data = stream.read(self.chunk_size, exception_on_overflow=False)
            
            if len(data) == 0:
                break
            
            if rec.AcceptWaveform(data):
                # Полная фраза распознана
                result = json.loads(rec.Result())
                text = result.get('text', '')
                if text:
                    yield text
            else:
                # Можно обрабатывать частичные результаты
                # partial = json.loads(rec.PartialResult())
                pass

    def stop(self):
        self.is_running = False