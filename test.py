# main.py — Голосовой ассистент с 2D-аватаром и Qwen
import pygame
import threading
from PIL import Image

from speech_to_text import LiveSpeechRecognizer
from nlp_dlm import generate_text
from tts import speak, stop_tts, warmup_tts  # ✅ Обновлённый импорт

# ================= CONFIG =================
WIDTH, HEIGHT = 1000, 1000
FPS = 60
# =========================================

# -------- GLOBAL STATE --------
speaking = False  # Флаг состояния аватара (говорит / молчит)

# -------- GIF LOADER --------
def load_gif(path):
    """Загружает GIF и возвращает списки кадров и длительностей."""
    gif = Image.open(path)
    frames = []
    durations = []
    try:
        while True:
            frame = gif.convert("RGBA")
            surf = pygame.image.fromstring(
                frame.tobytes(), frame.size, frame.mode
            )
            frames.append(pygame.transform.smoothscale(surf, (WIDTH, HEIGHT)))
            durations.append(gif.info.get("duration", 100))
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames, durations

# -------- SPEAK THREAD --------
def speak_thread(text):
    """Поток озвучки: управляет флагом анимации и вызывает TTS."""
    global speaking
    speaking = True
    try:
        speak(text)
    finally:
        speaking = False  # Сбрасывается даже при прерывании стопом

# -------- AVATAR WINDOW --------
def avatar_loop():
    """Основной цикл отрисовки Pygame с переключением GIF."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Avatar")
    clock = pygame.time.Clock()

    # Загрузка анимаций (проверь пути!)
    idle_frames, idle_dur = load_gif("gifs/not_speak.gif")
    talk_frames, talk_dur = load_gif("gifs/speak.gif")

    frames = idle_frames
    durations = idle_dur
    frame_idx = 0
    frame_time = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_tts()  # ✅ Мгновенная остановка звука и очереди
                break

        # ---- STATE SWITCH ----
        if speaking:
            if frames is not talk_frames:
                frames = talk_frames
                durations = talk_dur
                frame_idx = 0
                frame_time = 0
        else:
            if frames is not idle_frames:
                frames = idle_frames
                durations = idle_dur
                frame_idx = 0
                frame_time = 0

        # Анимация кадров
        frame_time += dt * 1000
        if frame_time >= durations[frame_idx]:
            frame_time = 0
            frame_idx = (frame_idx + 1) % len(frames)

        screen.fill((20, 20, 20))
        screen.blit(frames[frame_idx], (0, 0))
        pygame.display.flip()

    pygame.quit()

# -------- MAIN --------
def main():
    # Прогреваем соединение с edge-tts при старте (убирает лаг на первом ответе)
    warmup_tts()

    # Инициализация распознавания речи
    recognizer = LiveSpeechRecognizer(model_path="models/vosk-model-ru-0.42")

    # Запуск окна аватара в отдельном потоке
    avatar_thread = threading.Thread(target=avatar_loop, daemon=True)
    avatar_thread.start()

    # Основной цикл: слушаем → генерируем → озвучиваем
    for sentence in recognizer.listen():
        print("Вы:", sentence)

        # Генерация ответа через Qwen
        gen = generate_text(sentence, access_token=None)
        print("Бот:", gen)

        # Озвучка в фоне (не блокирует распознавание)
        threading.Thread(target=speak_thread, args=(gen,), daemon=True).start()

# -------- ENTRY --------
if __name__ == "__main__":
    main()