# JARVIS — Local Voice Assistant

Phase 1 of the build: the **brain** — LLM + tool-calling into your Proxmox
homelab (M630e). Voice I/O (wake word, STT, TTS) plugs in next as Phase 2.

## Architecture

```
orchestrator.py          <- conversation loop (LLM <-> tools)
llm/
  base.py                <- interface every backend implements
  ollama_client.py        <- Ollama backend (active by default)
  __init__.py              <- get_llm() factory, reads config.LLM_BACKEND
tools/
  proxmox.py               <- Proxmox API calls (M630e)
  registry.py               <- tool schemas + name->function map
config.py                    <- all settings, from .env
```

**The whole point of this structure:** `orchestrator.py` never imports
Ollama directly — it only calls `get_llm()`

## Setup

### 1. Install Ollama on your PC
Download from https://ollama.com, then pull the model:
```bash
ollama pull qwen3:8b
```
Confirm the GPU is being used — `ollama ps` should show GPU
layers, not 100% CPU.

Qwen3 has a "thinking mode" it can use for harder reasoning, the system
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
Proxmox Dashboard: **Datacenter > Permissions > API Tokens > Add**, role `PVEAuditor`.

### 4. Test it
```bash
python orchestrator.py
```
Try asking things like:
- "What's my server's CPU usage?"
- "Is Jellyfin running?"
- "List my containers"

This proves the LLM ↔ Proxmox tool-calling loop works before adding the
voice layer on top.

## Phase 2
- **faster-whisper** for STT (GPU-accelerated on the 1070)
- **Piper** for TTS
- **openWakeWord** so it's always listening for "Jarvis" without you
  pressing a button


## Voice mode setup (Phase 2.1)

Once text mode works, this adds the full talk-to-it .

### 1. Install voice dependencies
```bash
pip install -r requirements.txt
```
This now includes `sounddevice`, `openwakeword`, `faster-whisper`, and
`piper-tts`.

### 2. Download a Piper voice model
Piper needs a voice model file (not bundled — you pick a voice). Get one
from https://github.com/rhasspy/piper/blob/master/VOICES.md. 
You need both the `.onnx` file and
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

### 6. GPU-accelerated transcription
faster-whisper needs the CUDA Toolkit specifically (separate from your
NVIDIA display driver). **Install version 12.4 specifically** — not the
newest version — since that's what CTranslate2 (faster-whisper's backend)
is built against:
https://developer.nvidia.com/cuda-12-4-1-download-archive

After installing, fully restart
your terminal (new window, not just re-activating venv) so PATH updates
take effect.

Without this, `voice/stt.py` automatically falls back to CPU — slower,
but functional. GPU mode is a speed upgrade, not a requirement.

### 7. Qwen3's "thinking" mode
Qwen3 has an  reasoning mode that, left on, can burn through the
entire response token budget on internal thought before writing any
actual answer which results in silent empty responses. This is disabled
via Ollama's  `think: false` API parameter in
`llm/ollama_client.py` (a `/no_think` prompt instruction alone wasn't
reliable). If you ever see empty Jarvis responses return, check this
first.

**Expect this to need debugging** — mic selection, wake word sensitivity,
silence detection timing, and GPU memory sharing between Whisper and
Ollama are all things that  need tuning on a first run. That's
normal, same as the Proxmox permission issues earlier.

