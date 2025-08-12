import io
import wave
import numpy as np
from typing import Optional, Dict, Any, List
from .base import TTSBackend, AudioFormat
import logging

logger = logging.getLogger(__name__)


class CoquiTTSBackend(TTSBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Coqui TTS", config)
        self.tts = None
        self.model_name = config.get("model_name", "tts_models/en/ljspeech/tacotron2-DDC") if config else "tts_models/en/ljspeech/tacotron2-DDC"
        self.vocoder_name = config.get("vocoder_name", None) if config else None
        self.use_cuda = config.get("use_cuda", False) if config else False
        
    def initialize(self) -> bool:
        try:
            from TTS.api import TTS
            
            # Initialize TTS with specified model
            logger.info(f"Initializing Coqui TTS with model: {self.model_name}")
            
            if self.vocoder_name:
                self.tts = TTS(model_name=self.model_name, vocoder_name=self.vocoder_name, gpu=self.use_cuda)
            else:
                self.tts = TTS(model_name=self.model_name, gpu=self.use_cuda)
            
            self.is_initialized = True
            logger.info("Coqui TTS initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
            self.is_initialized = False
            return False
    
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
        
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize Coqui TTS backend")
        
        try:
            # Create temporary WAV file in memory
            wav_buffer = io.BytesIO()
            
            # Check if model supports multi-speaker
            if hasattr(self.tts, 'speakers') and self.tts.speakers and voice:
                # Multi-speaker model
                wav_data = self.tts.tts(text=text, speaker=voice, language=language)
            elif hasattr(self.tts, 'languages') and self.tts.languages and language:
                # Multi-language model
                wav_data = self.tts.tts(text=text, language=language)
            else:
                # Single speaker/language model
                wav_data = self.tts.tts(text=text)
            
            # Convert numpy array to WAV bytes
            if isinstance(wav_data, np.ndarray):
                # Normalize audio to 16-bit range
                wav_data = np.array(wav_data * 32767, dtype=np.int16)
                
                # Write WAV file
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.tts.synthesizer.output_sample_rate if hasattr(self.tts, 'synthesizer') else 22050)
                    wav_file.writeframes(wav_data.tobytes())
                
                wav_buffer.seek(0)
                return wav_buffer.read()
            else:
                # If TTS returns bytes directly
                return wav_data
                
        except Exception as e:
            logger.error(f"Synthesis failed with Coqui TTS: {e}")
            raise RuntimeError(f"Failed to synthesize speech: {e}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        if not self.is_initialized:
            self.initialize()
        
        voices = []
        try:
            if hasattr(self.tts, 'speakers') and self.tts.speakers:
                for speaker in self.tts.speakers:
                    voices.append({
                        "id": speaker,
                        "name": speaker,
                        "language": "multi",
                        "gender": "unknown"
                    })
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        
        return voices
    
    def get_available_languages(self) -> List[str]:
        if not self.is_initialized:
            self.initialize()
        
        languages = []
        try:
            if hasattr(self.tts, 'languages') and self.tts.languages:
                languages = self.tts.languages
        except Exception as e:
            logger.error(f"Failed to get languages: {e}")
        
        return languages if languages else ["en"]
    
    def is_available(self) -> bool:
        try:
            from TTS.api import TTS
            return True
        except ImportError:
            return False
    
    def cleanup(self) -> None:
        if self.tts:
            del self.tts
            self.tts = None
        self.is_initialized = False