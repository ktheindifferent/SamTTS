# Multi-Backend Offline TTS API

A unified HTTP API for multiple offline Text-to-Speech (TTS) backends. This API provides a consistent interface to synthesize speech using various TTS engines without requiring internet connectivity.

## Supported TTS Backends

1. **Coqui TTS** - High-quality neural TTS with multiple models (includes XTTS-v2)
2. **eSpeak** - Lightweight, multi-language speech synthesizer
3. **eSpeak-NG** - Next Generation of eSpeak with improved quality
4. **MaryTTS** - Modular, Java-based TTS platform
5. **pyttsx3** - Python TTS wrapper supporting multiple engines
6. **Festival** - General multi-lingual speech synthesis system

## Features

- Unified REST API for all TTS backends
- Auto-detection of available TTS engines
- Support for multiple voices and languages per backend
- Adjustable speech parameters (speed, pitch)
- Batch synthesis support
- Streaming audio output
- Comprehensive backend information endpoints

## Installation

### Prerequisites

Install system dependencies for the TTS backends you want to use:

```bash
# For eSpeak
sudo apt-get install espeak

# For eSpeak-NG
sudo apt-get install espeak-ng

# For Festival
sudo apt-get install festival

# For MaryTTS (requires Java)
sudo apt-get install default-jre
# Download MaryTTS from http://mary.dfki.de/
```

### Python Dependencies

```bash
# Clone the repository
cd /root/repo/multi_tts_api

# Install Python dependencies
pip install -r requirements.txt

# For Coqui TTS models (optional, for specific models)
# This will download models on first use
```

## Usage

### Starting the API Server

```bash
# Start with default settings
python -m uvicorn multi_tts_api.api:app --host 0.0.0.0 --port 8000

# Or run directly
python api.py

# With auto-reload for development
uvicorn multi_tts_api.api:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Health Check
```bash
GET /health
```

#### List Available Backends
```bash
GET /backends
```

#### Get Backend Information
```bash
GET /backends/{backend_id}
```

#### Get Available Voices
```bash
GET /voices/{backend_id}
```

#### Get Available Languages
```bash
GET /languages/{backend_id}
```

#### Synthesize Speech
```bash
POST /synthesize
Content-Type: application/json

{
  "text": "Hello, this is a test",
  "backend": "espeak",
  "language": "en",
  "speed": 1.0,
  "pitch": 1.0,
  "format": "wav"
}
```

#### Streaming Synthesis
```bash
POST /synthesize/stream
Content-Type: application/json

{
  "text": "Stream this audio",
  "backend": "coqui",
  "voice": "default",
  "format": "wav"
}
```

#### Batch Synthesis
```bash
POST /synthesize/batch
Content-Type: application/json

[
  {
    "text": "First text",
    "backend": "espeak",
    "language": "en"
  },
  {
    "text": "Second text",
    "backend": "festival",
    "voice": "voice_kal_diphone"
  }
]
```

### Example Usage with curl

```bash
# Simple synthesis with eSpeak
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "backend": "espeak"}' \
  --output speech.wav

# List all backends
curl http://localhost:8000/backends

# Get voices for Coqui TTS
curl http://localhost:8000/voices/coqui

# Stream audio
curl -X POST http://localhost:8000/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Streaming audio test", "backend": "espeak"}' \
  --output stream.wav
```

### Example Usage with Python

```python
import requests
import json

# API base URL
base_url = "http://localhost:8000"

# List available backends
response = requests.get(f"{base_url}/backends")
print("Available backends:", response.json())

# Synthesize speech
tts_request = {
    "text": "Hello from Python",
    "backend": "espeak",
    "language": "en",
    "speed": 1.2,
    "pitch": 0.9
}

response = requests.post(
    f"{base_url}/synthesize",
    json=tts_request
)

# Save audio file
with open("output.wav", "wb") as f:
    f.write(response.content)
```

## Configuration

### Backend-Specific Configuration

You can register backends with custom configuration:

```python
# Register Coqui TTS with specific model
POST /backends/register
{
  "backend_id": "coqui",
  "config": {
    "model_name": "tts_models/en/ljspeech/glow-tts",
    "vocoder_name": "vocoder_models/en/ljspeech/hifigan_v2",
    "use_cuda": false
  }
}

# Register MaryTTS with custom server
POST /backends/register
{
  "backend_id": "marytts",
  "config": {
    "host": "localhost",
    "port": 59125,
    "marytts_path": "/opt/marytts"
  }
}
```

## Backend Comparison

| Backend | Quality | Speed | Languages | Resource Usage | Features |
|---------|---------|-------|-----------|----------------|----------|
| Coqui TTS | Excellent | Slow-Medium | Many | High | Neural models, voice cloning |
| eSpeak | Fair | Very Fast | 50+ | Very Low | Compact, reliable |
| eSpeak-NG | Good | Very Fast | 100+ | Very Low | Improved quality over eSpeak |
| MaryTTS | Good | Medium | Multiple | Medium | Modular, customizable |
| pyttsx3 | Varies | Fast | Varies | Low | Cross-platform wrapper |
| Festival | Good | Medium | Multiple | Medium | Highly configurable |

## Troubleshooting

### Backend Not Available
- Ensure the TTS engine is installed on your system
- Check system PATH includes the TTS executable
- Verify permissions to execute the TTS program

### Coqui TTS Models
- Models are downloaded on first use
- Default model: `tts_models/en/ljspeech/tacotron2-DDC`
- Check available models: `tts --list_models`

### MaryTTS Server
- Requires Java Runtime Environment
- Default port: 59125
- Can run embedded or connect to external server

### Audio Quality Issues
- Adjust speed and pitch parameters
- Try different voices within the same backend
- Use higher quality backends like Coqui TTS for important applications

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Backends

1. Create a new backend class in `backends/` inheriting from `TTSBackend`
2. Implement required methods: `initialize`, `synthesize`, `get_available_voices`, etc.
3. Register the backend in `backend_manager.py`
4. Test the new backend

## License

This project integrates with various TTS engines, each with their own licenses:
- Coqui TTS: Mozilla Public License 2.0
- eSpeak/eSpeak-NG: GPL v3
- MaryTTS: LGPL v3
- Festival: Custom license (see Festival documentation)

## Contributing

Contributions are welcome! Please submit pull requests or open issues for:
- New TTS backend implementations
- Bug fixes
- Performance improvements
- Documentation updates