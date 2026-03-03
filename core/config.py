"""Configuration for local real-time assistant.

Adjust model paths and device settings here.
"""
from dataclasses import dataclass

@dataclass
class Config:
    SAMPLE_RATE: int = 16000  # Keep input at 16kHz for STT
    TTS_SAMPLE_RATE: int = 22050  # TTS can be higher
    CHANNELS: int = 1
    FRAME_MS: int = 30  # audio frame size in ms (20-40ms recommended)
    FRAME_SAMPLES: int = int(SAMPLE_RATE * FRAME_MS / 1000)
    VAD_AGGRESSIVENESS: int = 1  # Lowered from 2 for less aggressive speech detectionOLD_FRAMES: int = 40    # Hold VAD "speaking" for N frames after speech ends (more time)
    VAD_SILENCE_THRESHOLD: int = 40  # Frames of silence before end of utterance
    # For quick testing on first run use a small model; change to large-v2 for quality
    FASTER_WHISPER_MODEL: str = "large-v2"  # change to installed model
    OLLAMA_HOST: str = "http://127.0.0.1:11434"  # Ollama local API
    OLLAMA_MODEL: str = "gemma3:1b"
    # System prompt to make LLM behave as a friendly companion voice assistant
    OLLAMA_SYSTEM: str = """You are a friendly, empathetic voice companion named "Muse".
- Keep replies concise (1-3 sentences) and conversational.
- Use warm, natural language; occasionally ask one short follow-up question when appropriate.
- Bring gentle humor and curiosity, but never be rude or invasive.
- If the user shares a personal detail, remember it for future replies and refer to it briefly.
- If uncertain about a fact, ask a clarifying question instead of guessing.

Example interactions (few-shot):
User: "I'm feeling tired today."
Assistant: "I'm sorry to hear that — do you want a quick energizing tip or a calming exercise?"

User: "Tell me a joke."
Assistant: "Why don't scientists trust atoms? Because they make up everything. Want another one?"

Use this persona to generate responses suitable for spoken delivery. Do not include emojis.
"""
    PIPER_COMMAND: str = "C:\\Users\\Sefer\\Documents\\piper\\piper.exe"  # full path to Piper binary
    PIPER_MODEL: str = "C:\\Users\\Sefer\\Documents\\piper\\en_US-kristin-medium.onnx"  # Piper model - kristin works
    DEVICE: str = "cpu"  # or "cuda" - use cpu if no GPU
    INPUT_DEVICE: int = 1  # AT2020 USB microphone

config = Config()
