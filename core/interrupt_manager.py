"""Interrupt (barge-in) manager.

Exposes an asyncio.Event that other modules can wait on. When an interrupt
is triggered (e.g., VAD detects user while speaking), call `trigger()` to
signal all listeners and perform cleanup.
"""
import asyncio


class InterruptManager:
    def __init__(self):
        self._event = asyncio.Event()
        self._stop_event = asyncio.Event()  # Separate stop event for LLM

    def trigger(self):
        # set the event to signal cancellation
        self._event.set()

    def clear(self):
        self._event.clear()

    def get_event(self) -> asyncio.Event:
        # Return the same event every time
        return self._event
    
    def get_stop_event(self) -> asyncio.Event:
        """Return a separate event for signaling LLM to stop."""
        return self._stop_event
