import pyttsx3
import tempfile
import os
from typing import Optional, Dict, Any, List
from .base import TTSBackend, AudioFormat
import logging

logger = logging.getLogger(__name__)


class Pyttsx3Backend(TTSBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("pyttsx3", config)
        self.engine = None
        self.engine_id = config.get("engine_id", None) if config else None  # sapi5, nsss, espeak
        
    def initialize(self) -> bool:
        try:
            # Initialize pyttsx3 engine
            if self.engine_id:
                self.engine = pyttsx3.init(self.engine_id)
            else:
                self.engine = pyttsx3.init()
            
            # Set default properties
            self.engine.setProperty('rate', 150)  # Speed
            self.engine.setProperty('volume', 1.0)  # Volume
            
            self.is_initialized = True
            logger.info(f"pyttsx3 initialized with engine: {self.engine.proxy._driver.__class__.__name__}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
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
                raise RuntimeError("Failed to initialize pyttsx3 backend")
        
        try:
            # Set voice if specified
            if voice:
                voices = self.engine.getProperty('voices')
                for v in voices:
                    if v.id == voice or v.name == voice:
                        self.engine.setProperty('voice', v.id)
                        break
            
            # Set speed (rate in words per minute)
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', int(rate * speed))
            
            # Volume control
            volume = kwargs.get('volume', 1.0)
            self.engine.setProperty('volume', volume)
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_filename = tmp_file.name
            
            # Save speech to file
            self.engine.save_to_file(text, tmp_filename)
            self.engine.runAndWait()
            
            # Read the generated WAV file
            with open(tmp_filename, 'rb') as f:
                wav_data = f.read()
            
            # Clean up temporary file
            os.unlink(tmp_filename)
            
            return wav_data
            
        except Exception as e:
            logger.error(f"Synthesis failed with pyttsx3: {e}")
            # Clean up temporary file if it exists
            if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
            raise RuntimeError(f"Failed to synthesize speech: {e}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        if not self.is_initialized:
            self.initialize()
        
        voices = []
        try:
            for voice in self.engine.getProperty('voices'):
                # Extract language from voice ID or use default
                language = "unknown"
                if hasattr(voice, 'languages') and voice.languages:
                    language = voice.languages[0]
                elif 'en' in voice.id.lower():
                    language = "en"
                
                # Try to determine gender from voice name/id
                gender = "unknown"
                if 'female' in voice.name.lower() or 'female' in voice.id.lower():
                    gender = "female"
                elif 'male' in voice.name.lower() or 'male' in voice.id.lower():
                    gender = "male"
                
                voices.append({
                    "id": voice.id,
                    "name": voice.name,
                    "language": language,
                    "gender": gender
                })
                
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        
        return voices
    
    def get_available_languages(self) -> List[str]:
        voices = self.get_available_voices()
        languages = list(set(v["language"] for v in voices if v["language"] != "unknown"))
        return sorted(languages) if languages else ["en"]
    
    def is_available(self) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            del engine
            return True
        except:
            return False
    
    def cleanup(self) -> None:
        if self.engine:
            del self.engine
            self.engine = None
        self.is_initialized = False