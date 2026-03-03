"""TTS module integrating Piper (real implementation).

This module demonstrates sentence-based TTS chunking and streaming playback
by producing small audio buffers and placing them on the playback queue.
Uses Piper subprocess for real text-to-speech synthesis.
"""
import asyncio
import subprocess
import tempfile
import os
import numpy as np
import wave
import re
from typing import AsyncIterator
from .config import config


class TTSService:
    def __init__(self, playback_queue: asyncio.Queue):
        self.playback_queue = playback_queue
        self._cancel_event = asyncio.Event()

    async def speak_sentences(self, sentence_stream: AsyncIterator[str]):
        async for sentence in sentence_stream:
            if self._cancel_event.is_set():
                self._cancel_event.clear()
                continue
            # synthesize audio using Piper
            audio = await self._synthesize(sentence)
            if audio is None or len(audio) == 0:
                continue
            # chunk audio into small buffers (e.g., 100ms)
            sr = getattr(config, 'TTS_SAMPLE_RATE', 22050)
            chunk_ms = 100
            chunk_samples = int(sr * chunk_ms / 1000)
            for i in range(0, len(audio), chunk_samples):
                if self._cancel_event.is_set():
                    break
                await self.playback_queue.put(audio[i:i+chunk_samples])

    async def _synthesize(self, text: str) -> np.ndarray:
        """Synthesize text using Piper TTS."""
        # Remove emoji characters so the TTS engine does not read them aloud.
        # If removing emojis leaves an empty string, return a short silence/fallback.
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+",
            flags=re.UNICODE,
        )
        clean_text = emoji_pattern.sub('', text).strip()
        if not clean_text:
            return self._placeholder_synthesize(text)
        piper_cmd = config.PIPER_COMMAND
        model_path = getattr(config, 'PIPER_MODEL', None)
        
        # Try to find a default model if not configured
        if not model_path:
            possible_paths = [
                "C:\\Users\\Sefer\\Documents\\piper\\en_US-lessac-medium.onnx",
                "C:\\Users\\Sefer\\Documents\\piper\\en_US-kristin-medium.onnx",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
        
        if not model_path or not os.path.exists(piper_cmd):
            print(f"TTS: Piper not found at {piper_cmd} or model not configured")
            return self._placeholder_synthesize(text)
        
        try:
            # Create temp file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
                tmp_path = tmp_out.name
            
            # Run Piper with supported flags. Avoid using flags that some
            # Piper builds don't accept (like --pitch/--sample_rate).
            process = await asyncio.create_subprocess_exec(
                piper_cmd,
                '--model', model_path,
                '--output_file', tmp_path,
                '--debug',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                # Protect the subprocess communicate from cancellation so we
                # can cleanly kill the subprocess if the surrounding task
                # is cancelled. Use the cleaned text (emoji-free).
                stdout, stderr = await asyncio.shield(process.communicate(input=clean_text.encode('utf-8')))
            except asyncio.CancelledError:
                try:
                    process.kill()
                except Exception:
                    pass
                try:
                    await process.wait()
                except Exception:
                    pass
                return self._placeholder_synthesize(text)
            
            if process.returncode != 0:
                print(f"TTS: Piper error: {stderr.decode()}")
                return self._placeholder_synthesize(text)
            
            # Read WAV file
            if os.path.exists(tmp_path):
                with wave.open(tmp_path, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                os.remove(tmp_path)
                return audio
            else:
                print(f"TTS: Piper didn't produce output file")
                return self._placeholder_synthesize(text)
                
        except Exception as e:
            print(f"TTS: Synthesis failed: {e}")
            return self._placeholder_synthesize(text)

    def _placeholder_synthesize(self, text: str) -> np.ndarray:
        """Fallback placeholder when Piper is unavailable."""
        duration_s = max(0.5, min(5.0, 0.05 * len(text)))
        sr = 16000
        t = np.linspace(0, duration_s, int(sr*duration_s), False)
        wave = 0.03 * np.sin(2 * np.pi * 220 * t)
        return wave.astype('float32')

    def cancel(self):
        self._cancel_event.set()
