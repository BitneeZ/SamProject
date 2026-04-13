# tts.py — Потоковый edge-tts с конвейером и стабильным async-циклом
import asyncio
import edge_tts
import sounddevice as sd
import librosa
import numpy as np
import io
import threading
import time
import re
import queue
import warnings

warnings.filterwarnings('ignore', message='Unclosed client session')
warnings.filterwarnings('ignore', message='Task was destroyed')
warnings.filterwarnings('ignore', category=UserWarning)

# ==========================================
# ⚙️ НАСТРОЙКИ
# ==========================================
DEVICE_ID = None
VOICE = "ru-RU-DmitryNeural"
SAMPLE_RATE = 48000
RATE_BOOST = "+15%"
FIRST_CHUNK_LEN = 80  # Микро-чанк для мгновенного старта
NORMAL_CHUNK_LEN = 300  # Остальные чанки
# ==========================================

stop_event = threading.Event()

# -------- ПЕРСИСТЕНТНЫЙ ASYNCIO LOOP --------
_loop = None
_loop_lock = threading.Lock()


def _get_loop():
    global _loop
    with _loop_lock:
        if _loop is None or _loop.is_closed():
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, daemon=True, name="TTS-Loop").start()
        return _loop


def run_async(coro):
    """Запускает корутину в постоянном цикле и ждёт результат."""
    loop = _get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# -------- ТЕКСТОВЫЕ УТИЛИТЫ --------
def clean_rp_text(text: str) -> str:
    text = re.sub(r'\*[^*]*\*', '', text)
    text = re.sub(r'\.{3,}', ', ', text)
    text = re.sub(r'[«»"“”\-]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def split_text_smart(text: str) -> list[str]:
    """Первый чанк короткий, остальные — по предложениям."""
    if not text: return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, cur = [], ""

    for i, s in enumerate(sentences):
        limit = FIRST_CHUNK_LEN if (i == 0 and not cur) else NORMAL_CHUNK_LEN
        if len(cur) + len(s) + 1 > limit and cur:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = cur + " " + s if cur else s
    if cur.strip(): chunks.append(cur.strip())
    return chunks or [text]


def _apply_fade(audio: np.ndarray, ms: int = 8):
    samples = max(1, int(SAMPLE_RATE * ms / 1000))
    if len(audio) <= samples * 2: return audio
    fade_in = np.linspace(0, 1, samples, dtype=np.float32)
    fade_out = np.linspace(1, 0, samples, dtype=np.float32)
    audio[:samples] *= fade_in
    audio[-samples:] *= fade_out
    return audio


# -------- ГЕНЕРАЦИЯ ОДНОГО ЧАНКА --------
async def _generate_chunk_async(text: str):
    """Генерирует аудио для одного текстового куска и возвращает numpy-массив."""
    try:
        comm = edge_tts.Communicate(text, VOICE, rate=RATE_BOOST)
        mp3_data = bytearray()
        async for chunk in comm.stream():
            if stop_event.is_set(): return None
            if chunk["type"] == "audio":
                mp3_data.extend(chunk["data"])

        if not mp3_data: return None

        audio, _ = librosa.load(io.BytesIO(mp3_data), sr=SAMPLE_RATE, mono=True)
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = (audio / peak) * 0.85
        return audio
    except Exception as e:
        print(f"\n[Edge-TTS Error] {e}")
        return None


# -------- КОНВЕЙЕР: ПРОИЗВОДИТЕЛЬ + ПОТРЕБИТЕЛЬ --------
def _play_worker(audio_queue: queue.Queue):
    """Поток воспроизведения."""
    while True:
        item = audio_queue.get()
        if item is None: break
        if stop_event.is_set():
            audio_queue.task_done()
            break
        try:
            sd.play(item, samplerate=SAMPLE_RATE, device=DEVICE_ID, blocking=False)
            while sd.get_stream() is not None and sd.get_stream().active:
                if stop_event.is_set():
                    sd.stop()
                    break
                time.sleep(0.02)
        except Exception:
            pass
        audio_queue.task_done()


def _produce_chunks(text_chunks: list[str], audio_queue: queue.Queue):
    """Поток генерации: преобразует текст в аудио и кладёт в очередь."""
    print("🔊 Говорю...", end=" ", flush=True)
    for chunk_text in text_chunks:
        if stop_event.is_set(): break
        print("📡", end="", flush=True)

        try:
            audio = run_async(_generate_chunk_async(chunk_text))
            if audio is None:
                if stop_event.is_set(): break
                continue
            try:
                audio_queue.put(audio, timeout=2)
            except queue.Full:
                continue
        except Exception as e:
            print(f"\n[Gen Error] {e}")
            continue
        time.sleep(0.01)


def stream_tts(text: str):
    """Запускает конвейер: генерация и воспроизведение параллельно."""
    sd.stop()
    time.sleep(0.05)
    stop_event.clear()

    chunks = split_text_smart(clean_rp_text(text))
    if not chunks: return

    audio_queue = queue.Queue(maxsize=3)

    player = threading.Thread(target=_play_worker, args=(audio_queue,), daemon=True)
    player.start()

    _produce_chunks(chunks, audio_queue)

    audio_queue.put(None)
    player.join(timeout=2)
    print("\n✅ Готово.")


# -------- PUBLIC API --------
def speak(text: str):
    stream_tts(text)


def stop_tts():
    stop_event.set()
    sd.stop()


def warmup_tts():
    """Инициализирует цикл и греет соединение."""
    print("🔥 Инициализация TTS-системы...")
    _get_loop()
    try:
        run_async(asyncio.sleep(0))
        print("✅ TTS-конвейер готов\n")
    except Exception as e:
        print(f"⚠️ Тестовый запуск: {e}")