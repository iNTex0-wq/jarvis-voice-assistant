"""Wake word detection via openWakeWord — listens for "hey jarvis"."""
import numpy as np
from openwakeword.model import Model

from voice.audio_io import SAMPLE_RATE


class WakeWordListener:
    def __init__(self, wakeword_model: str = "hey_jarvis", threshold: float = 0.5):
        self.model = Model(wakeword_models=[wakeword_model], inference_framework="onnx")
        self.model_name = wakeword_model
        self.threshold = threshold

    def check_chunk(self, audio_chunk: np.ndarray) -> bool:
        prediction = self.model.predict(audio_chunk)
        score = prediction.get(self.model_name, 0.0)
        return score > self.threshold

    def listen_for_wake_word(self, chunk_ms: int = 80) -> None:
        import sounddevice as sd

        chunk_samples = int(SAMPLE_RATE * chunk_ms / 1000)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while True:
                chunk, _ = stream.read(chunk_samples)
                chunk = chunk.flatten()
                if self.check_chunk(chunk):
                    return
