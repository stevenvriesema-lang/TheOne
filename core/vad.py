"""VAD using Silero - much better than WebRTC."""
import numpy as np
import torch
import torchaudio
from .config import config

# Load Silero VAD model
try:
    silero_model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False
    )
    (get_speech_timestamps, _, _, _) = utils
    _HAS_SILERO = True
except Exception:
    _HAS_SILERO = False


class VADService:
    def __init__(self, aggressiveness: int = None):
        self.model = silero_model if _HAS_SILERO else None
        self.sample_rate = config.SAMPLE_RATE
        
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        if self.model is None:
            # Fallback: no VAD
            return True
            
        try:
            # Convert float32 to tensor
            audio_tensor = torch.from_numpy(audio_frame).float()
            
            # Ensure correct sample rate
            if len(audio_tensor.shape) > 1:
                audio_tensor = audio_tensor.mean(dim=1)
                
            # Get VAD prediction
            with torch.no_grad():
                speech_prob = self.model(audio_tensor, self.sample_rate).item()
            
            return speech_prob > 0.5
        except Exception:
            return True  # Default to speech on error
