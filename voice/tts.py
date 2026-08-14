"""Text-to-speech via Piper."""
import numpy as np

from voice.audio_io import play_audio


class Speaker:
    def __init__(self, model_path: str, config_path: str | None = None, speed: float = 0.8):
        """speed = Piper's length_scale. Lower is faster; 1.0 is the model's default pace."""
        from piper import PiperVoice

        self.voice = PiperVoice.load(model_path, config_path=config_path)
        self.speed = speed

        # some piper-tts versions want speed via SynthesisConfig, some don't support it at all
        self._syn_config = None
        try:
            from piper import SynthesisConfig
            self._syn_config = SynthesisConfig(length_scale=speed)
        except (ImportError, TypeError):
            pass

    def speak(self, text: str):
        if not text.strip():
            return

        chunks = []
        sample_rate = None

        if self._syn_config is not None:
            audio_iter = self.voice.synthesize(text, syn_config=self._syn_config)
        else:
            audio_iter = self.voice.synthesize(text)

        for audio_chunk in audio_iter:
            chunks.append(audio_chunk.audio_float_array)
            sample_rate = audio_chunk.sample_rate

        if not chunks:
            return

        audio = np.concatenate(chunks)
        play_audio(audio, sample_rate)
