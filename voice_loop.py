"""JARVIS Voice Loop — wake word -> record -> transcribe -> orchestrator
-> speak. Run this for the full voice experience; orchestrator.py still
works standalone in text mode for debugging."""
import os
import re
from datetime import datetime

from config import config
from orchestrator import Orchestrator
from voice.audio_io import record_until_silence, SAMPLE_RATE
from voice.stt import Transcriber
from voice.tts import Speaker
from voice.wake import WakeWordListener

PIPER_MODEL_PATH = "voices/en_GB-alan-medium.onnx"

CODE_BLOCK_PATTERN = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
GENERATED_CODE_DIR = "generated_code"

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

SPOKEN_SUBSTITUTIONS = [
    (re.compile(r"&"), " and "),
    (re.compile(r"%"), " percent"),
    (re.compile(r"@"), " at "),
]


def extract_and_strip_code(answer: str) -> str:
    """Saves code blocks to a file, prints them, and returns the answer
    with code stripped out — leaving just the part meant to be spoken."""
    code_blocks = CODE_BLOCK_PATTERN.findall(answer)

    if code_blocks:
        os.makedirs(GENERATED_CODE_DIR, exist_ok=True)
        for i, code in enumerate(code_blocks):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{GENERATED_CODE_DIR}/{timestamp}_{i}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code.strip())
            print(f"\n--- Code (saved to {filename}) ---\n{code.strip()}\n---\n")

    return CODE_BLOCK_PATTERN.sub("", answer).strip()


def clean_for_speech(text: str) -> str:
    """Strips markdown/emoji/symbols that TTS reads badly or not at all."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = EMOJI_PATTERN.sub("", text)
    for pattern, replacement in SPOKEN_SUBSTITUTIONS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def main():
    print(f"[{config.ASSISTANT_NAME}] Loading models... (this takes a moment)")

    wake_listener = WakeWordListener(wakeword_model="hey_jarvis")
    transcriber = Transcriber(model_size="small.en", device="cuda")
    speaker = Speaker(model_path=PIPER_MODEL_PATH, speed=0.8)
    orchestrator = Orchestrator()

    print(f"[{config.ASSISTANT_NAME}] Ready. Say 'Hey Jarvis' to start.\n")

    while True:
        wake_listener.listen_for_wake_word()
        print("[wake word detected] Listening...")

        audio = record_until_silence(sample_rate=SAMPLE_RATE)
        if len(audio) < SAMPLE_RATE * 0.3:
            print("[too short, ignoring]\n")
            continue

        text = transcriber.transcribe(audio, sample_rate=SAMPLE_RATE)
        if not text:
            print("[couldn't hear anything, ignoring]\n")
            continue
        print(f"You said: {text}")

        answer = orchestrator.ask(text)
        print(f"{config.ASSISTANT_NAME}: {answer}\n")

        speakable = extract_and_strip_code(answer)
        speakable = clean_for_speech(speakable)
        speaker.speak(speakable)


if __name__ == "__main__":
    main()
