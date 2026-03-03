"""Simple test for LLM and TTS pipeline."""
import asyncio
import sys
sys.path.insert(0, '.')

from core.llm import LLMService
from core.tts import TTSService
from core.config import config

async def test():
    print("Testing LLM + TTS pipeline...")
    
    # Create queues
    token_q = asyncio.Queue()
    playback_q = asyncio.Queue()
    
    # Test LLM
    llm = LLMService(token_q)
    stop_event = asyncio.Event()
    
    print(f"Calling Ollama with model {config.OLLAMA_MODEL}...")
    
    # Start LLM task
    llm_task = asyncio.create_task(llm.stream_response("Say 'hello' in one word", stop_event))
    
    # Collect tokens
    tokens = []
    while True:
        try:
            tok = await asyncio.wait_for(token_q.get(), timeout=5.0)
            if tok is None:
                print("LLM finished")
                break
            tokens.append(tok)
            print(f"Token: {tok[:50]}...")
        except asyncio.TimeoutError:
            print("Timeout waiting for tokens")
            break
    
    full_text = "".join(tokens)
    print(f"Full response: {full_text[:200]}...")
    
    # Test TTS
    print("\nTesting TTS...")
    tts = TTSService(playback_q)
    
    async def test_sentences():
        yield "Hello, this is a test."
    
    tts_task = asyncio.create_task(tts.speak_sentences(test_sentences()))
    
    # Wait for TTS to produce audio
    audio_chunks = 0
    while True:
        try:
            chunk = await asyncio.wait_for(playback_q.get(), timeout=2.0)
            if chunk is None:
                break
            audio_chunks += 1
            print(f"TTS chunk {audio_chunks}: {len(chunk)} samples")
        except asyncio.TimeoutError:
            print("Timeout waiting for TTS")
            break
    
    print(f"\nTest complete! Got {audio_chunks} audio chunks from TTS")

asyncio.run(test())
