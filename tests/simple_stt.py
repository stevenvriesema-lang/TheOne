"""Simple STT test - listen and print when sentence is complete."""
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

print("Loading Whisper model...")
model = WhisperModel("base", device="cpu")
print("Model loaded! Speak now...")

SAMPLE_RATE = 16000
FRAME_SAMPLES = 480

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    
    audio = indata[:, 0].copy()
    audio = audio * 5.0
    audio = np.clip(audio, -1.0, 1.0)
    
    level = np.abs(audio).mean()
    print(f"Level: {level:.4f}", end="")
    
    if level > 0.02:
        print(" <- SPEECH!")
        result = model.transcribe(audio, beam_size=5)
        texts = []
        for seg in result:
            if hasattr(seg, 'text'):
                texts.append(seg.text)
        text = " ".join(texts)
        if text.strip():
            print(f">>> {text}")
    else:
        print()

print(f"Sample rate: {SAMPLE_RATE}")
print("Listening... (press Enter to stop)")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=FRAME_SAMPLES,
    device=1,
    callback=audio_callback
):
    input()
