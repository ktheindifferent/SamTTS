from fastapi import FastAPI, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import io
import json
import logging
from .backend_manager import BackendManager
from .backends.base import AudioFormat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Backend TTS API",
    description="A unified API for multiple offline Text-to-Speech backends",
    version="1.0.0"
)

# Initialize backend manager
backend_manager = BackendManager()


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    backend: str = Field(..., description="TTS backend to use")
    voice: Optional[str] = Field(None, description="Voice ID to use")
    language: Optional[str] = Field(None, description="Language code")
    speed: float = Field(1.0, description="Speech speed multiplier", ge=0.1, le=3.0)
    pitch: float = Field(1.0, description="Pitch multiplier", ge=0.5, le=2.0)
    format: str = Field("wav", description="Output audio format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, this is a test of the multi-backend TTS API.",
                "backend": "espeak",
                "language": "en",
                "speed": 1.0,
                "pitch": 1.0,
                "format": "wav"
            }
        }


class BackendConfig(BaseModel):
    backend_id: str = Field(..., description="Backend identifier")
    config: Optional[Dict[str, Any]] = Field(None, description="Backend-specific configuration")


@app.on_event("startup")
async def startup_event():
    # Auto-detect and register available backends
    detected = backend_manager.auto_detect_backends()
    if detected:
        logger.info(f"Auto-detected backends: {detected}")
    else:
        logger.warning("No backends were auto-detected. Please register backends manually.")
    
    # Try to register Coqui TTS with default model if available
    if "coqui" not in detected:
        backend_manager.register_backend("coqui", {
            "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
            "use_cuda": False
        })


@app.on_event("shutdown")
async def shutdown_event():
    backend_manager.cleanup()


@app.get("/", response_class=JSONResponse)
async def root():
    return {
        "message": "Multi-Backend TTS API",
        "endpoints": {
            "GET /backends": "List available TTS backends",
            "GET /backends/{backend_id}": "Get backend information",
            "POST /synthesize": "Synthesize speech",
            "POST /synthesize/stream": "Synthesize speech (streaming)",
            "GET /voices/{backend_id}": "Get available voices for a backend",
            "GET /languages/{backend_id}": "Get available languages for a backend",
            "POST /backends/register": "Register a new backend",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    backends = backend_manager.list_backends()
    return {
        "status": "healthy" if backends else "degraded",
        "available_backends": len(backends),
        "backends": backends
    }


@app.get("/backends")
async def list_backends():
    return {
        "backends": backend_manager.list_backends(),
        "details": backend_manager.get_all_backends_info()
    }


@app.get("/backends/{backend_id}")
async def get_backend_info(backend_id: str):
    info = backend_manager.get_backend_info(backend_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Backend '{backend_id}' not found")
    return info


@app.post("/backends/register")
async def register_backend(config: BackendConfig):
    success = backend_manager.register_backend(config.backend_id, config.config)
    if success:
        return {"message": f"Backend '{config.backend_id}' registered successfully"}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to register backend '{config.backend_id}'"
        )


@app.get("/voices/{backend_id}")
async def get_voices(backend_id: str):
    backend = backend_manager.get_backend(backend_id)
    if not backend:
        raise HTTPException(status_code=404, detail=f"Backend '{backend_id}' not found")
    
    voices = backend.get_available_voices()
    return {"backend": backend_id, "voices": voices}


@app.get("/languages/{backend_id}")
async def get_languages(backend_id: str):
    backend = backend_manager.get_backend(backend_id)
    if not backend:
        raise HTTPException(status_code=404, detail=f"Backend '{backend_id}' not found")
    
    languages = backend.get_available_languages()
    return {"backend": backend_id, "languages": languages}


@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    try:
        # Get audio format
        try:
            audio_format = AudioFormat(request.format.lower())
        except ValueError:
            audio_format = AudioFormat.WAV
        
        # Synthesize speech
        audio_data = backend_manager.synthesize(
            backend_id=request.backend,
            text=request.text,
            voice=request.voice,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            output_format=audio_format
        )
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        
        # Return audio data
        media_type = f"audio/{audio_format.value}"
        if audio_format == AudioFormat.WAV:
            media_type = "audio/wav"
        
        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{audio_format.value}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/stream")
async def synthesize_speech_stream(request: TTSRequest):
    try:
        # Get audio format
        try:
            audio_format = AudioFormat(request.format.lower())
        except ValueError:
            audio_format = AudioFormat.WAV
        
        # Synthesize speech
        audio_data = backend_manager.synthesize(
            backend_id=request.backend,
            text=request.text,
            voice=request.voice,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            output_format=audio_format
        )
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        
        # Stream audio data
        media_type = f"audio/{audio_format.value}"
        if audio_format == AudioFormat.WAV:
            media_type = "audio/wav"
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=speech.{audio_format.value}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/batch")
async def synthesize_batch(requests: List[TTSRequest]):
    results = []
    errors = []
    
    for i, request in enumerate(requests):
        try:
            audio_data = backend_manager.synthesize(
                backend_id=request.backend,
                text=request.text,
                voice=request.voice,
                language=request.language,
                speed=request.speed,
                pitch=request.pitch
            )
            
            if audio_data:
                # Convert to base64 for JSON response
                import base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                results.append({
                    "index": i,
                    "success": True,
                    "audio": audio_b64,
                    "format": request.format
                })
            else:
                errors.append({
                    "index": i,
                    "error": "Failed to synthesize speech"
                })
                
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e)
            })
    
    return {
        "results": results,
        "errors": errors,
        "total": len(requests),
        "successful": len(results),
        "failed": len(errors)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)