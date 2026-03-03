"""Better STT test with buffering."""
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

print("Loading Whisper model...")
model = WhisperModel("base", device="cpu")
print("Model loaded! Speak now...")

SAMPLE_RATE = 16000
FRAME_SAMPLES = 480
BUFFER_SIZE = 20  # About 600ms of audio before transcribing

audio_buffer = []

def audio_callback(indata, frames, time, status):
    global audio_buffer
    if status:
        print(f"Status: {status}")
    
    audio = indata[:, 0].copy()
    audio = audio * 5.0
    audio = np.clip(audio, -1.0, 1.0)
    
    level = np.abs(audio).mean()
    
    if level > 0.02:
        # Speech detected - add to buffer
        audio_buffer.append(audio)
        
        # When buffer is full, transcribe
        if len(audio_buffer) >= BUFFER_SIZE:
            full_audio = np.concatenate(audio_buffer)
            print(f"\nTranscribing {len(full_audio)} samples...")
            result = model.transcribe(full_audio, beam_size=5)
            texts = []
            for seg in result:
                if hasattr(seg, 'text'):
                    texts.append(seg.text)
            text = " ".join(texts)
            if text.strip():
                print(f">>> {text}")
            audio_buffer = []  # Clear buffer
    else:
        # No speech - clear buffer
        if audio_buffer:
            audio_buffer = []

print(f"Sample rate: {SAMPLE_RATE}, Buffer: {BUFFER_SIZE} frames")
print("Listening... (press Enter to stop)")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=FRAME_SAMPLES,
    device=1,
    callback=audio_callback,
    latency="low"
):
    input()
