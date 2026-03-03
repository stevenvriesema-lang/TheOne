"""Audio capture module.

Runs a non-blocking sounddevice input stream in a thread and forwards audio
frames to an asyncio queue using loop.call_soon_threadsafe.

The callback must be minimal and never block.
"""
import sounddevice as sd
import numpy as np
import threading
import asyncio
from typing import Callable
from .config import config


class AudioInput:
    def __init__(self, loop: asyncio.AbstractEventLoop, audio_queue: asyncio.Queue):
        self.loop = loop
        self.audio_queue = audio_queue
        self.stream = None
        self._stop_event = threading.Event()

    def _callback(self, indata, frames, time, status):
        try:
            # copy to avoid referencing transient buffer
            data = indata[:, 0].copy()
            # Apply gain amplification (5x)
            gain = 5.0
            data = data * gain
            # Clip to prevent overflow
            data = np.clip(data, -1.0, 1.0)
            # push to asyncio queue from thread
            self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, data)
        except Exception:
            # swallow exceptions in callback
            pass

    def start(self):
        device = getattr(config, 'INPUT_DEVICE', None)
        self.stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            blocksize=config.FRAME_Sself.stream.start()
        try:
        AMPLES,

        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self._stop_event.set()


if __name__ == "__main__":
    # simple manual test
    import asyncio

    async def main():
        q = asyncio.Queue()
        ai = AudioInput(asyncio.get_event_loop(), q)
        ai.start()
        for _ in range(10):
            frame = await q.get()
            print("got frame", frame.shape)
        ai.stop()

    asyncio.run(main())
