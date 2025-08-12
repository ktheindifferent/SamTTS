import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List
from .base import TTSBackend, AudioFormat
import logging

logger = logging.getLogger(__name__)


class ESpeakNGBackend(TTSBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("eSpeak-NG", config)
        self.espeak_ng_path = config.get("espeak_ng_path", "espeak-ng") if config else "espeak-ng"
        self.default_voice = config.get("default_voice", "en") if config else "en"
        
    def initialize(self) -> bool:
        try:
            # Check if espeak-ng is available
            result = subprocess.run(
                [self.espeak_ng_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.is_initialized = True
                logger.info(f"eSpeak-NG initialized: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"eSpeak-NG not available: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Failed to initialize eSpeak-NG: {e}")
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
                raise RuntimeError("Failed to initialize eSpeak-NG backend")
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_filename = tmp_file.name
            
            # Build espeak-ng command
            cmd = [self.espeak_ng_path]
            
            # Set voice/language
            if voice:
                cmd.extend(["-v", voice])
            elif language:
                cmd.extend(["-v", language])
            else:
                cmd.extend(["-v", self.default_voice])
            
            # Set speed (words per minute, default is 175)
            wpm = int(175 * speed)
            cmd.extend(["-s", str(wpm)])
            
            # Set pitch (0-99, default is 50)
            pitch_val = int(50 * pitch)
            pitch_val = max(0, min(99, pitch_val))
            cmd.extend(["-p", str(pitch_val)])
            
            # Additional parameters for better quality
            amplitude = kwargs.get("amplitude", 100)
            cmd.extend(["-a", str(amplitude)])
            
            # Set gap between words (optional)
            gap = kwargs.get("gap", 0)
            if gap > 0:
                cmd.extend(["-g", str(gap)])
            
            # Output to WAV file
            cmd.extend(["-w", tmp_filename])
            
            # Add text
            cmd.append(text)
            
            # Execute espeak-ng
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"eSpeak-NG synthesis failed: {result.stderr}")
            
            # Read the generated WAV file
            with open(tmp_filename, 'rb') as f:
                wav_data = f.read()
            
            # Clean up temporary file
            os.unlink(tmp_filename)
            
            return wav_data
            
        except Exception as e:
            logger.error(f"Synthesis failed with eSpeak-NG: {e}")
            # Clean up temporary file if it exists
            if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
            raise RuntimeError(f"Failed to synthesize speech: {e}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        if not self.is_initialized:
            self.initialize()
        
        voices = []
        try:
            # Get list of available voices
            result = subprocess.run(
                [self.espeak_ng_path, "--voices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        voice_id = parts[1]
                        voice_name = parts[3] if len(parts) > 3 else voice_id
                        language = parts[1].split('+')[0] if '+' in parts[1] else parts[1]
                        
                        # Try to determine gender from voice variant
                        gender = "unknown"
                        if '+f' in voice_id or '+female' in voice_id:
                            gender = "female"
                        elif '+m' in voice_id or '+male' in voice_id:
                            gender = "male"
                        
                        voices.append({
                            "id": voice_id,
                            "name": voice_name,
                            "language": language,
                            "gender": gender
                        })
                        
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        
        return voices
    
    def get_available_languages(self) -> List[str]:
        voices = self.get_available_voices()
        languages = list(set(v["language"] for v in voices))
        return sorted(languages)
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.espeak_ng_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False