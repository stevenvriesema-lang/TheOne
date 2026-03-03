"""Audio playback module with immediate-stop capability.

Plays PCM float32 mono audio from an asyncio queue. Supports immediate
stop/flush via `stop_playback()` which sets an asyncio.Event.
"""
import sounddevice as sd
import asyncio
import numpy as np
from .config import config


class AudioOutput:
    def __init__(self, loop: asyncio.AbstractEventLoop, playback_queue: asyncio.Queue):
        self.loop = loop
        self.queue = playback_queue
        self._playing = False
        self._stop_flag = asyncio.Event()

    async def play_loop(self):
        self._playing = True
        # Use TTS sample rate for output
        output_sr = getattr(config, 'TTS_SAMPLE_RATE', config.SAMPLE_RATE)
        with sd.OutputStream(samplerate=output_sr, channels=1, dtype='float32') as stream:
            while self._playing:
                self._stop_flag.clear()
                chunk = await self.queue.get()
                if chunk is None:
                    break
                # chunk is expected as numpy float32 array
                if self._stop_flag.is_set():
                    continue
                try:
                    stream.write(np.asarray(chunk, dtype='float32'))
                except Exception:
                    pass

    def stop_playback(self):
        self._stop_flag.set()

    def shutdown(self):
        self._playing = False
