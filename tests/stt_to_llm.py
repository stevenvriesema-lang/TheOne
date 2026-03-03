"""Simplified STT -> LLM -> TTS test harness.

Listens on microphone, detects utterance boundaries with WebRTC VAD,
transcribes completed utterances with faster-whisper, sends final text to
the LLM, and plays the TTS response. This variant avoids partial/speculative
streaming for stability.
"""
import argparse
import asyncio
import numpy as np
import sounddevice as sd

from core.llm import LLMService
from core.tts import TTSService
from core import memory, history


async def play_from_queue(playback_q: asyncio.Queue, sample_rate: int = 22050):
    try:
        with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
            while True:
                chunk = await playback_q.get()
                if chunk is None:
                    break
                try:
                    stream.write(np.asarray(chunk, dtype='float32'))
                except Exception:
                    pass
    except Exception as e:
        print('Audio playback failed:', e)


async def handle_text_and_respond(text: str):
    lowered = text.lower()
    import re
    m = re.search(r"my name is\s+([A-Za-zÀ-ÖØ-öø-ÿ'-]+)", lowered)
    if m:
        name = m.group(1).strip().capitalize()
        memory.update_memory('name', name)
        print(f"Memory: saved name={name}")

    mem = memory.get_memory_summary()
    recent = history.get_recent_summary(3)
    prompt_parts = []
    if mem:
        prompt_parts.append(f"User facts: {mem}")
    if recent:
        prompt_parts.append(f"Conversation (recent): {recent}")
    prompt = '\n'.join(prompt_parts + [f"User: {text}"]) if prompt_parts else text

    print('Sending to LLM:', prompt)
    token_q = asyncio.Queue()
    playback_q = asyncio.Queue()

    llm = LLMService(token_q)
    stop_event = asyncio.Event()
    llm_task = asyncio.create_task(llm.stream_response(prompt, stop_event))

    tts = TTSService(playback_q)

    async def sentence_stream():
        buf = ''
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

    play_task = asyncio.create_task(play_from_queue(playback_q))
    tts_task = asyncio.create_task(tts.speak_sentences(sentence_stream()))

    await llm_task
    await tts_task
    await playback_q.put(None)
    await play_task


def make_vad_detector(aggressiveness: int):
    import webrtcvad

    vad = webrtcvad.Vad(max(0, min(3, aggressiveness)))

    def is_speech_frame(frame_float: np.ndarray, sample_rate: int = 16000):
        pcm16 = (frame_float * 32767.0).astype(np.int16).tobytes()
        try:
            return vad.is_speech(pcm16, sample_rate)
        except Exception:
            return False

    return is_speech_frame


async def main_async(args):
    SAMPLE_RATE = 16000
    FRAME_MS = args.frame_ms
    FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)

    loop = asyncio.get_event_loop()
    frames_q: asyncio.Queue = asyncio.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print('Input status:', status)
        loop.call_soon_threadsafe(frames_q.put_nowait, indata.copy())

    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, blocksize=FRAME_SAMPLES, dtype='float32', channels=1, callback=callback, device=args.device_index)
        stream.start()
    except Exception as e:
        print('Could not open input stream:', e)
        return

    is_speech = make_vad_detector(args.aggressiveness)

    from faster_whisper import WhisperModel
    print('Loading model:', args.model)
    model = WhisperModel(args.model, device=args.device)
    print('Model loaded. Listening... (Ctrl-C to stop)')

    in_speech = False
    silence_frames_needed = max(1, int(args.silence_ms / FRAME_MS))
    silence_counter = 0
    buffer_frames = []

    try:
        while True:
            frame = await frames_q.get()
            mono = frame[:, 0] if frame.ndim > 1 else frame

            speech = is_speech(mono, SAMPLE_RATE)
            if speech:
                if not in_speech:
                    in_speech = True
                    buffer_frames = []
                    silence_counter = 0
                    print('VAD: speech started')
                buffer_frames.append(mono)
            else:
                if in_speech:
                    silence_counter += 1
                    buffer_frames.append(mono)
                    if silence_counter >= silence_frames_needed:
                        in_speech = False
                        audio = np.concatenate(buffer_frames).astype('float32')
                        print('STT: end detected — transcribing...')

                        def transcribe_block():
                            try:
                                if args.language:
                                    return model.transcribe(audio, language=args.language)
                                return model.transcribe(audio)
                            except Exception as e:
                                return e

                        res = await loop.run_in_executor(None, transcribe_block)

                        texts = []
                        try:
                            if isinstance(res, Exception):
                                raise res
                            segments = None
                            if isinstance(res, tuple) and len(res) == 2:
                                segments, _ = res
                            elif hasattr(res, 'segments'):
                                segments = getattr(res, 'segments')
                            elif hasattr(res, '__iter__') and not isinstance(res, (str, bytes)):
                                segments = res
                            else:
                                segments = [res]

                            for seg in segments:
                                if seg is None:
                                    continue
                                if isinstance(seg, dict):
                                    texts.append(seg.get('text', ''))
                                else:
                                    texts.append(getattr(seg, 'text', str(seg)))
                        except Exception as e:
                            print('Transcription error:', e)
                            buffer_frames = []
                            silence_counter = 0
                            continue

                        final_text = ' '.join(t for t in texts if t).strip()
                        if final_text:
                            history.add_turn('User', final_text)
                            await handle_text_and_respond(final_text)
                            history.add_turn('Assistant', '<response>')

                        buffer_frames = []
                        silence_counter = 0
                else:
                    pass
    except KeyboardInterrupt:
        print('\nStopped by user')
    finally:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='tiny')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--language', default='en')
    parser.add_argument('--aggressiveness', type=int, default=2)
    parser.add_argument('--frame-ms', type=int, default=30)
    parser.add_argument('--silence-ms', type=int, default=700)
    parser.add_argument('--device-index', type=int, default=None)
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
