import pygame
import threading
from PIL import Image

from speech_to_text import LiveSpeechRecognizer 
from nlp_dlm import generate_text, get_access_token
from tts import speak, stop_queue

# ================= CONFIG =================
WIDTH, HEIGHT = 1000, 1000
FPS = 60
# =========================================

# -------- GLOBAL STATE --------
speaking = False

# -------- GIF LOADER --------
def load_gif(path):
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
    global speaking
    speaking = True
    try:
        speak(text)
    finally:
        speaking = False

# -------- AVATAR WINDOW --------
def avatar_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Avatar")
    clock = pygame.time.Clock()

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
                stop_queue()
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
    recognizer = LiveSpeechRecognizer(
        model_path="models/vosk-model-small-ru-0.22"
    )

    avatar_thread = threading.Thread(
        target=avatar_loop, daemon=True
    )
    avatar_thread.start()

    for sentence in recognizer.listen():
        print("Вы:", sentence)

        gen = generate_text(sentence, get_access_token())
        print("Бот:", gen)

        threading.Thread(
            target=speak_thread,
            args=(gen,),
            daemon=True
        ).start()

# -------- ENTRY --------
if __name__ == "__main__":
    main()
