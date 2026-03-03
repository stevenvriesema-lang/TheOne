"""Direct test of full pipeline: LLM -> TTS -> Audio playback."""
import asyncio
import sys
sys.path.insert(0, '.')

import sounddevice as sd
from core.llm import LLMService
from core.tts import TTSService

async def test():
    print("=== Full Pipeline Test ===")
    
    token_q = asyncio.Queue()
    playback_q = asyncio.Queue()
    
    # Start LLM
    llm = LLMService(token_q)
    stop_event = asyncio.Event()
    llm_task = asyncio.create_task(llm.stream_response("Say hello in a friendly way", stop_event))
    
    # Start TTS
    tts = TTSService(playback_q)
    
    async def sentence_stream():
        buf = ""
        while True:
            tok = await token_q.get()
            if tok is None:
                break
            buf += tok
            if any(c in buf for c in '.!?'):
                idx = max(buf.rfind('.'), buf.rfind('!'), buf.rfind('?'))
                sentence = buf[:idx+1].strip()
                buf = buf[idx+1:]
                if sentence:
                    yield sentence
        if buf.strip():
            yield buf.strip()
    
    tts_task = asyncio.create_task(tts.speak_sentences(sentence_stream()))
    
    # Play audio directly
    print("Starting audio playback...")
    with sd.OutputStream(samplerate=22050, channels=1, dtype='float32') as stream:
        while True:
            try:
                chunk = await asyncio.wait_for(playback_q.get(), timeout=3.0)
                if chunk is None:
                    print("End of audio")
                    break
                stream.write(chunk)
                print(f"Played: {len(chunk)} samples")
            except asyncio.TimeoutError:
                print("Timeout - stopping")
                break
    
    print("=== Test Complete ===")

asyncio.run(test())
