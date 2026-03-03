# Local Real-Time Conversational Voice Agent (Prototype)

This repository contains a modular prototype for a fully-local, low-latency
conversational voice agent for Windows (no Docker/WSL/cloud). It demonstrates
an async, queue-based pipeline with audio capture, VAD, streaming STT, LLM
streaming, TTS chunking, and immediate barge-in handling.

Structure
- core/config.py
- core/audio_input.py
- core/audio_output.py
- core/vad.py
- core/stt.py
- core/llm.py
- core/tts.py
- core/state_machine.py
- core/interrupt_manager.py
- main.py

Quick start (prototype)
1. Create a Python 3.11 venv and activate it.
2. Install requirements:

```bash
python -m pip install -r requirements.txt
```

3. Ensure local Ollama and Piper (or alternatives) are installed and running.

4. Run the prototype:

```bash
python main.py
```

Notes
- Many integrations are placeholder stubs meant to be replaced with real
  faster-whisper streaming decode, Ollama streaming parsing, and Piper
  subprocess streaming. The code focuses on correct async architecture,
  non-blocking audio callbacks, and barge-in handling.

Extension points
- Replace _dummy_decode in `core/stt.py` with faster-whisper streaming API.
- Parse Ollama streaming responses in `core/llm.py` and forward tokens.
- Replace _synthesize in `core/tts.py` with real Piper subprocess that streams
  PCM frames to `playback_queue`.
