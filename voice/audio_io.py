"""Mic capture and speaker playback."""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1


def list_devices():
    print(sd.query_devices())


def record_seconds(seconds: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=CHANNELS, dtype="float32")
    sd.wait()
    return audio.flatten()


def record_until_silence(
    sample_rate: int = SAMPLE_RATE,
    silence_threshold: float = 0.01,
    silence_duration: float = 1.2,
    max_duration: float = 15.0,
) -> np.ndarray:
    """Records until you stop talking, or max_duration as a safety cap."""
    chunk_size = int(sample_rate * 0.1)
    silence_chunks_needed = int(silence_duration / 0.1)
    max_chunks = int(max_duration / 0.1)

    frames = []
    silent_count = 0
    heard_speech = False

    with sd.InputStream(samplerate=sample_rate, channels=CHANNELS, dtype="float32") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()
            frames.append(chunk)

            volume = np.abs(chunk).mean()
            if volume > silence_threshold:
                heard_speech = True
                silent_count = 0
            else:
                silent_count += 1

            if heard_speech and silent_count >= silence_chunks_needed:
                break

    return np.concatenate(frames) if frames else np.array([], dtype="float32")


def play_audio(audio: np.ndarray, sample_rate: int):
    sd.play(audio, samplerate=sample_rate)
    sd.wait()
