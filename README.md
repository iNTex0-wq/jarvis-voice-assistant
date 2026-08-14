# JARVIS — Local Voice Assistant

Phase 1 of the build: the **brain** — LLM + tool-calling into your Proxmox
homelab (M630e). Voice I/O (wake word, STT, TTS) plugs in next as Phase 2.

## Architecture

```
orchestrator.py          <- conversation loop (LLM <-> tools)
llm/
  base.py                <- interface every backend implements
  ollama_client.py        <- Ollama backend (active by default)
  claude_client.py        <- Claude API backend (ready, unused for now)
  __init__.py              <- get_llm() factory, reads config.LLM_BACKEND
tools/
  proxmox.py               <- Proxmox API calls (M630e)
  registry.py               <- tool schemas + name->function map
config.py                    <- all settings, from .env
```

**The whole point of this structure:** `orchestrator.py` never imports
Ollama or Claude directly — it only calls `get_llm()`. Swapping brains
later is a one-line change in `.env` (`LLM_BACKEND=claude`), nothing else
in the code changes.

## Setup

### 1. Install Ollama on your PC
Download from https://ollama.com, then pull the model:
```bash
ollama pull qwen3:8b
```
Confirm the GTX 1070 (8GB) is being used — `ollama ps` should show GPU
layers, not 100% CPU.

Qwen3 has a "thinking mode" it can use for harder reasoning — the system
prompt in `orchestrator.py` sends `/no_think` so it answers directly and
fast, which matters for voice. If you ever want it to actually reason
through something complex, you can drop that directive for that query.

### 2. Python environment
```bash
cd jarvis
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
```
Fill in your Proxmox host/token. To create a read-only API token on the
M630e: **Datacenter > Permissions > API Tokens > Add**, role `PVEAuditor`.

### 4. Test it (text mode, no voice yet)
```bash
python orchestrator.py
```
Try asking things like:
- "What's my server's CPU usage?"
- "Is Jellyfin running?"
- "List my containers"

This proves the LLM ↔ Proxmox tool-calling loop works before adding the
voice layer on top.

## What's next (Phase 2)
- **faster-whisper** for STT (GPU-accelerated on the 1070)
- **Piper** for TTS
- **openWakeWord** so it's always listening for "Jarvis" without you
  pressing a button
- Later: Raspberry Pi as a satellite mic/speaker in your room, streaming
  audio to this PC instead of using the PC's own mic directly

## Voice mode setup (Phase 2)

Once text mode works, this adds the full talk-to-it experience.

### 1. Install voice dependencies
```bash
pip install -r requirements.txt
```
This now includes `sounddevice`, `openwakeword`, `faster-whisper`, and
`piper-tts`. If any of these fail to install, tell me the error — audio
libs sometimes need OS-level dependencies on Windows.

### 2. Download a Piper voice model
Piper needs a voice model file (not bundled — you pick a voice). Get one
from https://github.com/rhasspy/piper/blob/master/VOICES.md — a good
starting pick is `en_US-lessac-medium`. You need both the `.onnx` file and
its matching `.onnx.json` config file. Put both in a `voices/` folder in
your jarvis directory:
```
jarvis/voices/en_US-lessac-medium.onnx
jarvis/voices/en_US-lessac-medium.onnx.json
```

### 3. First run — openWakeWord will download its model automatically
The first time you run voice mode, openWakeWord downloads its wake-word
detection models (a few MB) automatically. This needs internet the first
time only.

### 4. Check your microphone
```python
from voice.audio_io import list_devices
list_devices()
```
Run that in a Python shell to see available input devices. sounddevice
uses your system default mic unless you configure otherwise — if it
picks the wrong one, tell me and we'll pin a specific device index.

### 5. Run it
```bash
python voice_loop.py
```
Say **"Hey Jarvis"**, wait for "Listening...", then ask your question.
It'll transcribe, think, answer, and speak back.

### 6. GPU-accelerated transcription (optional but recommended)
faster-whisper needs the CUDA Toolkit specifically (separate from your
NVIDIA display driver). **Install version 12.4 specifically** — not the
newest version — since that's what CTranslate2 (faster-whisper's backend)
is built against:
https://developer.nvidia.com/cuda-12-4-1-download-archive

Multiple CUDA Toolkit versions can coexist fine (e.g. having 13.x already
installed doesn't need to be removed). After installing, fully restart
your terminal (new window, not just re-activating venv) so PATH updates
take effect.

Without this, `voice/stt.py` automatically falls back to CPU — slower,
but functional. GPU mode is a speed upgrade, not a requirement.

### 7. Known gotcha: Qwen3's "thinking" mode
Qwen3 has an internal reasoning mode that, left on, can burn through the
entire response token budget on internal thought before writing any
actual answer — resulting in silent empty responses. This is disabled
via Ollama's native `think: false` API parameter in
`llm/ollama_client.py` (a `/no_think` prompt instruction alone wasn't
reliable). If you ever see empty Jarvis responses return, check this
first.

**Expect this to need debugging** — mic selection, wake word sensitivity,
silence detection timing, and GPU memory sharing between Whisper and
Ollama are all things that commonly need tuning on a first run. That's
normal, same as the Proxmox permission issues earlier.

## Switching to Claude API later
1. `pip install anthropic`
2. In `.env`: set `LLM_BACKEND=claude` and `ANTHROPIC_API_KEY=sk-ant-...`
3. That's it — same tools, same orchestrator, same everything else.
