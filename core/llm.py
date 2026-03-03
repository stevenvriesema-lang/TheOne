"""LLM streaming client for Ollama (prototype).

Uses a simple HTTP streaming reader to fetch tokens from the Ollama local API.
This implementation parses newline-delimited JSON events and pushes the
response text pieces to the provided token queue.
"""
import asyncio
import aiohttp
import json
from .config import config


class LLMService:
    def __init__(self, token_queue: asyncio.Queue):
        self.token_queue = token_queue

    async def stream_response(self, prompt: str, stop_event: asyncio.Event, model: str | None = None):
        url = f"{config.OLLAMA_HOST}/api/generate"
        use_model = model or getattr(config, 'OLLAMA_MODEL', 'gemma3:1b')

        system_prompt = getattr(config, 'OLLAMA_SYSTEM', None)
        payload = {
            "model": use_model,
            "prompt": prompt,
            "stream": True,
            "system": system_prompt,
            "options": {"temperature": 0.7},
        }

        buffer = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    async for chunk in resp.content.iter_any():
                        if stop_event.is_set():
                            break
                        try:
                            text = chunk.decode(errors='ignore')
                        except Exception:
                            text = ''

                        if not text:
                            continue

                        buffer += text
                        # extract complete JSON lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                response_text = data.get('response', '')
                                if response_text:
                                    await self.token_queue.put(response_text)
                            except json.JSONDecodeError:
                                # incomplete JSON; prepend back and break
                                buffer = line + '\n' + buffer
                                break

        except Exception as e:
            print(f"LLM error: {e}")
        finally:
            # Signal end of LLM response
            await self.token_queue.put(None)
            stop_event.set()
