import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List
from .base import TTSBackend, AudioFormat
import logging

logger = logging.getLogger(__name__)


class FestivalBackend(TTSBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Festival", config)
        self.festival_path = config.get("festival_path", "festival") if config else "festival"
        self.default_voice = config.get("default_voice", "voice_kal_diphone") if config else "voice_kal_diphone"
        
    def initialize(self) -> bool:
        try:
            # Check if festival is available
            result = subprocess.run(
                ["echo", "(quit)" , "|", self.festival_path, "--batch"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.is_initialized = True
                logger.info("Festival initialized successfully")
                return True
            else:
                logger.error(f"Festival not available: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Festival: {e}")
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
                raise RuntimeError("Failed to initialize Festival backend")
        
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as txt_file:
                txt_filename = txt_file.name
                txt_file.write(text)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_filename = wav_file.name
            
            # Build Festival script
            voice_cmd = voice if voice else self.default_voice
            
            # Create Festival commands
            festival_commands = f"""
({voice_cmd})
(Parameter.set 'Duration_Stretch {1.0/speed})
(set! duffint_params '((start {50 * pitch}) (end {50 * pitch})))
(tts_file "{txt_filename}" 'auto)
(utt.save.wave (utt.synth (Utterance Text "{text}")) "{wav_filename}" 'riff)
(quit)
"""
            
            # Write Festival commands to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scm', delete=False) as scm_file:
                scm_filename = scm_file.name
                scm_file.write(festival_commands)
            
            # Execute Festival
            result = subprocess.run(
                [self.festival_path, "-b", scm_filename],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Festival synthesis failed: {result.stderr}")
            
            # Read the generated WAV file
            with open(wav_filename, 'rb') as f:
                wav_data = f.read()
            
            # Clean up temporary files
            os.unlink(txt_filename)
            os.unlink(wav_filename)
            os.unlink(scm_filename)
            
            return wav_data
            
        except Exception as e:
            logger.error(f"Synthesis failed with Festival: {e}")
            # Clean up temporary files if they exist
            for filename in ['txt_filename', 'wav_filename', 'scm_filename']:
                if filename in locals() and os.path.exists(locals()[filename]):
                    os.unlink(locals()[filename])
            raise RuntimeError(f"Failed to synthesize speech: {e}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        voices = [
            {"id": "voice_kal_diphone", "name": "Kal (US English)", "language": "en-US", "gender": "male"},
            {"id": "voice_rab_diphone", "name": "Rab (British English)", "language": "en-GB", "gender": "male"},
            {"id": "voice_don_diphone", "name": "Don (British English)", "language": "en-GB", "gender": "male"},
            {"id": "voice_ked_diphone", "name": "Ked (US English)", "language": "en-US", "gender": "male"},
            {"id": "voice_el_diphone", "name": "El (Spanish)", "language": "es", "gender": "male"},
            {"id": "voice_pc_diphone", "name": "PC (Italian)", "language": "it", "gender": "male"},
        ]
        
        # Try to get actual available voices from Festival
        if self.is_initialized or self.initialize():
            try:
                result = subprocess.run(
                    ["echo", "(voice.list)", "|", self.festival_path, "--batch"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout:
                    # Parse voice list from output
                    voice_list = result.stdout.strip()
                    # This would need more sophisticated parsing
                    logger.debug(f"Festival voices: {voice_list}")
                    
            except Exception as e:
                logger.error(f"Failed to get Festival voices: {e}")
        
        return voices
    
    def get_available_languages(self) -> List[str]:
        return ["en-US", "en-GB", "es", "it"]
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["echo", "(quit)", "|", self.festival_path, "--batch"],
                shell=True,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False