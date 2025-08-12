# SamTTS - Multi-Backend Offline Text-to-Speech API

A unified HTTP REST API providing access to multiple offline Text-to-Speech (TTS) engines through a single interface. Built on top of 🐸Coqui TTS and other leading TTS technologies.

## 🚀 Features

- **Unified API** - Single HTTP interface for multiple TTS backends
- **Offline Operation** - No internet connectivity required
- **Multiple Engines** - Support for Coqui TTS, eSpeak, eSpeak-NG, MaryTTS, pyttsx3, and Festival
- **Auto-Detection** - Automatic detection of available TTS engines
- **Streaming & Batch** - Real-time streaming and batch synthesis support
- **Voice & Language Support** - Multiple voices and languages per backend
- **Adjustable Parameters** - Control speed, pitch, and other speech parameters

## 🎯 Quick Start

### Start the API Server
```bash
cd multi_tts_api
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### Synthesize Speech
```bash
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "backend": "espeak"}' \
  --output speech.wav
```

## 📋 Supported TTS Backends

| Backend | Quality | Speed | Languages | Features |
|---------|---------|-------|-----------|----------|
| **Coqui TTS** | Excellent | Medium | 20+ | Neural models, voice cloning |
| **eSpeak** | Fair | Very Fast | 50+ | Lightweight, reliable |
| **eSpeak-NG** | Good | Very Fast | 100+ | Improved quality |
| **MaryTTS** | Good | Medium | Multiple | Modular, customizable |
| **pyttsx3** | Varies | Fast | Varies | Cross-platform wrapper |
| **Festival** | Good | Medium | Multiple | Highly configurable |

## 📖 API Documentation

### Core Endpoints

#### List Available Backends
```bash
GET /backends
```

#### Get Backend Information
```bash
GET /backends/{backend_id}
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
```

#### Batch Synthesis
```bash
POST /synthesize/batch
```

For detailed API documentation, see [`multi_tts_api/README.md`](multi_tts_api/README.md).

## 🛠️ Installation

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
```

### Python Dependencies

```bash
# Clone the repository
git clone [your-repo-url]
cd SamTTS

# Install Python dependencies
cd multi_tts_api
pip install -r requirements.txt
```

## 🎭 Backend Details

### Coqui TTS
Based on the original 🐸TTS library with support for:
- High-performance Deep Learning models (Tacotron2, Glow-TTS, VITS, YourTTS)
- Neural vocoders (HiFiGAN, MelGAN, WaveRNN)
- Multi-speaker synthesis and voice cloning
- 20+ languages with pretrained models

### Other Backends
- **eSpeak/eSpeak-NG**: Lightweight, rule-based synthesis
- **MaryTTS**: Modular Java-based platform
- **pyttsx3**: Cross-platform TTS wrapper
- **Festival**: Configurable speech synthesis system

## 💻 Usage Examples

### Python Client
```python
import requests

# Start the API server first
# python -m uvicorn multi_tts_api.api:app --host 0.0.0.0 --port 8000

base_url = "http://localhost:8000"

# List available backends
response = requests.get(f"{base_url}/backends")
backends = response.json()
print("Available backends:", backends)

# Synthesize with eSpeak
tts_request = {
    "text": "Hello from SamTTS!",
    "backend": "espeak",
    "language": "en",
    "speed": 1.2
}

response = requests.post(f"{base_url}/synthesize", json=tts_request)
with open("output.wav", "wb") as f:
    f.write(response.content)
```

### Command Line Interface
```bash
# List available backends
curl http://localhost:8000/backends

# Synthesize speech with different backends
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Fast synthesis", "backend": "espeak"}' \
  --output fast.wav

curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "High quality synthesis", "backend": "coqui"}' \
  --output quality.wav

# Batch synthesis
curl -X POST http://localhost:8000/synthesize/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"text": "First sentence", "backend": "espeak"},
    {"text": "Second sentence", "backend": "festival"}
  ]' \
  --output batch.zip
```

## 📁 Project Structure
```
├── multi_tts_api/           # Main API application
│   ├── api.py              # FastAPI application and endpoints
│   ├── backend_manager.py  # Backend management and orchestration
│   ├── backends/           # TTS backend implementations
│   │   ├── base.py        # Abstract base class for backends
│   │   ├── coqui.py       # Coqui TTS backend
│   │   ├── espeak.py      # eSpeak backend
│   │   ├── espeak_ng.py   # eSpeak-NG backend
│   │   ├── festival.py    # Festival backend
│   │   ├── marytts.py     # MaryTTS backend
│   │   └── pyttsx3.py     # pyttsx3 backend
│   ├── requirements.txt    # Python dependencies
│   ├── run_server.py      # Server startup script
│   ├── test_api.py        # API test suite
│   └── README.md          # Detailed API documentation
├── TTS/                    # Original Coqui TTS library
└── README.md              # This file
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- New TTS backend implementations
- Performance optimizations
- Additional audio format support
- Better error handling and logging
- Extended language support

## 📄 License

This project builds upon multiple open-source TTS libraries:
- **Coqui TTS**: Mozilla Public License 2.0
- **eSpeak/eSpeak-NG**: GPL v3  
- **MaryTTS**: LGPL v3
- **Festival**: Custom license

See individual backend documentation for specific license requirements.
