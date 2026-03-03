"""Diagnostic test for faster-whisper STT."""
import numpy as np
import sys

# Test if faster-whisper works
try:
    from faster_whisper import WhisperModel
    print("faster-whisper imported successfully")
except Exception as e:
    print(f"Failed to import faster-whisper: {e}")
    sys.exit(1)

# Load model
print("Loading tiny model...")
model = WhisperModel("tiny", device="cpu")
print("Model loaded successfully")

# Create test audio - 1 second of silence (should still produce some output or empty)
sample_rate = 16000
duration = 1.0
test_audio = np.zeros(int(sample_rate * duration), dtype=np.float32)

print(f"Test audio shape: {test_audio.shape}, duration: {duration}s")

# Transcribe
print("Transcribing...")
result = model.transcribe(test_audio, beam_size=5)
print(f"Result type: {type(result)}")

# Handle different return types
if hasattr(result, 'segments'):
    segments = result.segments
elif isinstance(result, tuple):
    segments = result[0]
else:
    segments = result

texts = []
for seg in segments:
    if hasattr(seg, 'text'):
        texts.append(seg.text)
    elif isinstance(seg, dict):
        texts.append(seg.get('text', ''))

full_text = " ".join(texts)
print(f"Transcribed text: '{full_text}'")

# Test with actual speech-like audio (random noise as placeholder)
print("\n--- Testing with noise audio ---")
noise_audio = np.random.randn(int(sample_rate * 2)).astype(np.float32) * 0.1
result2 = model.transcribe(noise_audio, beam_size=5)
if hasattr(result2, 'text'):
    print(f"Noise result: '{result2.text}'")
elif hasattr(result2, 'segments'):
    for seg in result2.segments:
        print(f"Segment: {seg.text}")

print("\nDiagnostic complete!")
