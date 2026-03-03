"""Simple version of main.py for text-mode testing."""
import asyncio
import argparse
import sounddevice as sd
from core.llm import LLMService
from core.tts import TTSService

async def main(text_input: str):
    print(f"=== Simple Text Mode ===")
    print(f"Input: {text_input}")
    
    # Create queues
    token_q = asyncio.Queue()
    playback_q = asyncio.Queue()
    
    # Start LLM
    llm = LLMService(token_q)
    stop_event = asyncio.Event()
    llm_task = asyncio.create_task(llm.stream_response(text_input, stop_event))
    
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
    
    print("=== Done ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.text))
