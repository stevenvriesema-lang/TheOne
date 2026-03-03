"""Simple conversation state machine.

States: Listening, Thinking, Speaking, Interrupted, Idle
Transitions are explicit via methods.
"""
from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    INTERRUPTED = auto()


class ConversationState:
    def __init__(self):
        self.state = State.IDLE

    def set_listening(self):
        self.state = State.LISTENING

    def set_thinking(self):
        self.state = State.THINKING

    def set_speaking(self):
        self.state = State.SPEAKING

    def set_interrupted(self):
        self.state = State.INTERRUPTED

    def set_idle(self):
        self.state = State.IDLE
