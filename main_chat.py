"""Interactive CLI chat: type messages, get LLM response spoken via TTS.

Run:
  python main_chat.py

Type `/exit` or `/quit` to leave.
"""
import asyncio
import sounddevice as sd
from core.llm import LLMService
from core.tts import TTSService
from core import memory, history
import re


async def handle_single_turn(text: str):
    # record user in short-term history and update simple memory heuristics
    history.add_turn('User', text)
    lowered = text.lower()
    m = re.search(r"my name is\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)", lowered)
    if m:
        name = m.group(1).strip().capitalize()
        memory.update_memory('name', name)
        print(f"Memory: saved name={name}")

    # build prompt with memory and recent history so the LLM sees context
    mem = memory.get_memory_summary()
    recent = history.get_recent_summary(6)
    prompt_parts = []
    if mem:
        prompt_parts.append(f"User facts: {mem}")
    if recent:
        prompt_parts.append(f"Conversation (recent): {recent}")
    prompt = '\n'.join(prompt_parts + [f"User: {text}"]) if prompt_parts else text

    token_source = asyncio.Queue()
    tts_token_q = asyncio.Queue()
    playback_q = asyncio.Queue()

    llm = LLMService(token_source)
    stop_event = asyncio.Event()
    llm_task = asyncio.create_task(llm.stream_response(prompt, stop_event))

    tts = TTSService(playback_q)

    # collect assistant tokens so we can add the assistant reply to history
    response_parts: list[str] = []

    async def token_distributor():
        while True:
            tok = await token_source.get()
            if tok is None:
                await tts_token_q.put(None)
                break
            # forward to tts queue and collect for history
            await tts_token_q.put(tok)
            response_parts.append(tok)

    distributor_task = asyncio.create_task(token_distributor())

    async def sentence_stream():
        buf = ''
        while True:
            tok = await tts_token_q.get()
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

    async def playback_consumer():
        try:
            with sd.OutputStream(samplerate=22050, channels=1, dtype='float32') as stream:
                while True:
                    chunk = await playback_q.get()
                    if chunk is None:
                        break
                    try:
                        stream.write(chunk)
                    except Exception:
                        pass
        except Exception as e:
            print('Audio playback failed:', e)

    play_task = asyncio.create_task(playback_consumer())

    # Wait for LLM/TTS to finish
    await llm_task
    await distributor_task
    await tts_task

    # Signal playback consumer to finish and wait for it
    await playback_q.put(None)
    await play_task

    # record assistant reply in history
    assistant_text = ''.join(response_parts).strip()
    if assistant_text:
        history.add_turn('Assistant', assistant_text)


async def chat_loop():
    print('Interactive chat. Type /exit to quit.')

    msg_q: asyncio.Queue = asyncio.Queue()

    async def worker():
        while True:
            text = await msg_q.get()
            if text is None:
                break
            try:
                await handle_single_turn(text)
            except Exception as e:
                print('Error handling turn:', e)

    worker_task = asyncio.create_task(worker())

    try:
        while True:
            try:
                user = await asyncio.to_thread(input, 'You: ')
            except (EOFError, KeyboardInterrupt):
                print('\nExiting')
                break
            if not user:
                continue
            if user.strip().lower() in ('/exit', '/quit'):
                print('Goodbye')
                break
            # enqueue message and continue accepting input immediately
            await msg_q.put(user)
            print('Queued message')
    finally:
        await msg_q.put(None)
        await worker_task


def main():
    asyncio.run(chat_loop())


if __name__ == '__main__':
    main()
