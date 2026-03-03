"""Record audio then transcribe after pressing Enter."""
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import wave

print("Loading Whisper model...")
model = WhisperModel("base", device="cpu")
print("Model loaded!")

SAMPLE_RATE = 16000
CHANNELS = 1
FILENAME = "test_recording.wav"

print(f"\nRecording... Speak now! (press Enter to stop)")
recording = []

def callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    recording.append(indata.copy())

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    blocksize=1024,
    device=1,
    callback=callback
):
    input()

# Save recording
audio_data = np.concatenate(recording, axis=0)
audio_data = audio_data.flatten()
audio_int16 = (audio_data * 32767).astype(np.int16)

print(f"Saved {len(audio_data)} samples to {FILENAME}")

with wave.open(FILENAME, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_int16.tobytes())

print("\nTranscribing...")
result = model.transcribe(FILENAME)
texts = []
for seg in result:
    if hasattr(seg, 'text'):
        texts.append(seg.text)
final_text = " ".join(texts)
print(f"\n>>> {final_text}")
