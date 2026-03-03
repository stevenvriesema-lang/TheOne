"""Test TTS with actual audio playback."""
import asyncio
import sys
sys.path.insert(0, '.')

import sounddevice as sd
from core.tts import TTSService
from core.config import config

async def test_with_playback():
    print("Testing TTS with audio playback...")
    
    playback_q = asyncio.Queue()
    tts = TTSService(playback_q)
    
    # Create sentence stream
    async def sentences():
        yield "Hello, this is a test of the text to speech system."
    
    # Start TTS synthesis in background
    tts_task = asyncio.create_task(tts.speak_sentences(sentences()))
    
    # Play audio as it comes in
    with sd.OutputStream(samplerate=16000, channels=1, dtype='float32') as stream:
        while True:
            try:
                chunk = await asyncio.wait_for(playback_q.get(), timeout=2.0)
                if chunk is None:
                    break
                stream.write(chunk)
                print(f"Played chunk: {len(chunk)} samples")
            except asyncio.TimeoutError:
                print("Timeout - stopping")
                break
    
    print("Test complete!")

asyncio.run(test_with_playback())
