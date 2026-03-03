"""Simple mic test - just record and print audio levels."""
import sounddevice as sd
import numpy as np
import queue
import threading

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    # Print audio level
    level = np.abs(indata).mean()
    print(f"Audio level: {level:.4f} | ", end="")
    if level > 0.01:
        print("SPEECH DETECTED!")
    else:
        print("...")

print("Starting mic test... Speak now!")
with sd.InputStream(
    samplerate=16000,
    channels=1,
    callback=audio_callback,
    blocksize=480  # 30ms at 16kHz
):
    input()  # Wait for Enter key
print("Stopped.")
