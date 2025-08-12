from typing import Dict, List, Optional, Any
from .backends.base import TTSBackend
from .backends.coqui_tts import CoquiTTSBackend
from .backends.espeak import ESpeakBackend
from .backends.espeak_ng import ESpeakNGBackend
from .backends.marytts import MaryTTSBackend
from .backends.pyttsx3_backend import Pyttsx3Backend
from .backends.festival import FestivalBackend
import logging

logger = logging.getLogger(__name__)


class BackendManager:
    def __init__(self):
        self.backends: Dict[str, TTSBackend] = {}
        self.available_backends = {
            "coqui": CoquiTTSBackend,
            "espeak": ESpeakBackend,
            "espeak-ng": ESpeakNGBackend,
            "marytts": MaryTTSBackend,
            "pyttsx3": Pyttsx3Backend,
            "festival": FestivalBackend,
        }
    
    def register_backend(self, backend_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        if backend_id not in self.available_backends:
            logger.error(f"Unknown backend: {backend_id}")
            return False
        
        try:
            backend_class = self.available_backends[backend_id]
            backend = backend_class(config)
            
            if backend.is_available():
                if backend.initialize():
                    self.backends[backend_id] = backend
                    logger.info(f"Successfully registered backend: {backend_id}")
                    return True
                else:
                    logger.warning(f"Backend {backend_id} is available but failed to initialize")
            else:
                logger.warning(f"Backend {backend_id} is not available on this system")
                
        except Exception as e:
            logger.error(f"Failed to register backend {backend_id}: {e}")
        
        return False
    
    def auto_detect_backends(self) -> List[str]:
        detected = []
        for backend_id, backend_class in self.available_backends.items():
            try:
                backend = backend_class()
                if backend.is_available():
                    if self.register_backend(backend_id):
                        detected.append(backend_id)
                        logger.info(f"Auto-detected and registered: {backend_id}")
            except Exception as e:
                logger.debug(f"Could not auto-detect {backend_id}: {e}")
        
        return detected
    
    def get_backend(self, backend_id: str) -> Optional[TTSBackend]:
        return self.backends.get(backend_id)
    
    def list_backends(self) -> List[str]:
        return list(self.backends.keys())
    
    def get_backend_info(self, backend_id: str) -> Optional[Dict[str, Any]]:
        backend = self.get_backend(backend_id)
        if backend:
            return backend.get_info()
        return None
    
    def get_all_backends_info(self) -> Dict[str, Dict[str, Any]]:
        info = {}
        for backend_id, backend in self.backends.items():
            info[backend_id] = backend.get_info()
        return info
    
    def synthesize(
        self,
        backend_id: str,
        text: str,
        **kwargs
    ) -> Optional[bytes]:
        backend = self.get_backend(backend_id)
        if not backend:
            raise ValueError(f"Backend {backend_id} not found or not initialized")
        
        return backend.synthesize(text, **kwargs)
    
    def cleanup(self):
        for backend in self.backends.values():
            try:
                backend.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up backend {backend.name}: {e}")
        self.backends.clear()