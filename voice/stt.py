"""Speech-to-text via faster-whisper, GPU-accelerated on the 1070."""
import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "small.en", device: str = "cuda", compute_type: str = "int8"):
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            print(f"[stt] GPU init failed ({e}), falling back to CPU")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        segments, _ = self.model.transcribe(audio, language="en", beam_size=1, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
