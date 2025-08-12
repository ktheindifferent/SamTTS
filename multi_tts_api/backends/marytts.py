import requests
import subprocess
import time
import os
from typing import Optional, Dict, Any, List
from .base import TTSBackend, AudioFormat
import logging

logger = logging.getLogger(__name__)


class MaryTTSBackend(TTSBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("MaryTTS", config)
        self.host = config.get("host", "localhost") if config else "localhost"
        self.port = config.get("port", 59125) if config else 59125
        self.marytts_path = config.get("marytts_path", "/opt/marytts") if config else "/opt/marytts"
        self.server_process = None
        self.base_url = f"http://{self.host}:{self.port}"
        
    def initialize(self) -> bool:
        try:
            # First check if MaryTTS server is already running
            if self._check_server():
                self.is_initialized = True
                logger.info("MaryTTS server is already running")
                return True
            
            # Try to start MaryTTS server
            if os.path.exists(os.path.join(self.marytts_path, "bin", "marytts-server")):
                logger.info("Starting MaryTTS server...")
                self.server_process = subprocess.Popen(
                    [os.path.join(self.marytts_path, "bin", "marytts-server")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for server to start (max 30 seconds)
                for _ in range(30):
                    time.sleep(1)
                    if self._check_server():
                        self.is_initialized = True
                        logger.info("MaryTTS server started successfully")
                        return True
                
                logger.error("MaryTTS server failed to start within timeout")
                return False
            else:
                logger.warning("MaryTTS not found at specified path. Server must be running externally.")
                return self._check_server()
                
        except Exception as e:
            logger.error(f"Failed to initialize MaryTTS: {e}")
            self.is_initialized = False
            return False
    
    def _check_server(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/version", timeout=2)
            return response.status_code == 200
        except:
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
                raise RuntimeError("Failed to initialize MaryTTS backend")
        
        try:
            # Prepare parameters for MaryTTS
            params = {
                "INPUT_TEXT": text,
                "INPUT_TYPE": "TEXT",
                "OUTPUT_TYPE": "AUDIO",
                "AUDIO": "WAVE_FILE",
                "LOCALE": language or "en_US",
            }
            
            if voice:
                params["VOICE"] = voice
            
            # Speed control (prosody rate)
            if speed != 1.0:
                params["effect_Rate_selected"] = "on"
                params["effect_Rate_parameters"] = f"durScale:{1/speed}"
            
            # Pitch control
            if pitch != 1.0:
                params["effect_F0Scale_selected"] = "on"
                params["effect_F0Scale_parameters"] = f"f0Scale:{pitch}"
            
            # Make request to MaryTTS server
            response = requests.get(
                f"{self.base_url}/process",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                raise RuntimeError(f"MaryTTS synthesis failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Synthesis failed with MaryTTS: {e}")
            raise RuntimeError(f"Failed to synthesize speech: {e}")
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        if not self.is_initialized:
            self.initialize()
        
        voices = []
        try:
            response = requests.get(f"{self.base_url}/voices", timeout=5)
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 3:
                            voice_id = parts[0]
                            locale = parts[1]
                            gender = parts[2]
                            
                            voices.append({
                                "id": voice_id,
                                "name": voice_id,
                                "language": locale,
                                "gender": gender.lower()
                            })
                            
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        
        return voices
    
    def get_available_languages(self) -> List[str]:
        voices = self.get_available_voices()
        languages = list(set(v["language"] for v in voices))
        return sorted(languages)
    
    def is_available(self) -> bool:
        return self._check_server() or os.path.exists(os.path.join(self.marytts_path, "bin", "marytts-server"))
    
    def cleanup(self) -> None:
        if self.server_process:
            logger.info("Stopping MaryTTS server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
        self.is_initialized = False