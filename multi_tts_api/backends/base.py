from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import io
import wave
import numpy as np


class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class TTSBackend(ABC):
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.is_initialized = False
        
    @abstractmethod
    def initialize(self) -> bool:
        pass
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
        output_format: AudioFormat = AudioFormat.WAV,
        **kwargs
    ) -> bytes:
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        pass
    
    @abstractmethod
    def get_available_languages(self) -> List[str]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def cleanup(self) -> None:
        pass
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "available": self.is_available(),
            "voices": self.get_available_voices(),
            "languages": self.get_available_languages(),
            "config": self.config
        }
    
    @staticmethod
    def create_wav_bytes(audio_data: np.ndarray, sample_rate: int = 22050) -> bytes:
        audio_data = np.array(audio_data * 32767, dtype=np.int16)
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()