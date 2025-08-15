# SamTTS Codebase Documentation

## Project Overview

SamTTS is a comprehensive multi-backend offline Text-to-Speech (TTS) API system built on top of 🐸Coqui TTS and other leading TTS technologies. It provides a unified HTTP REST API interface for accessing multiple TTS engines without requiring internet connectivity.

### Key Features
- **Unified API**: Single HTTP interface for multiple TTS backends
- **Offline Operation**: Complete offline functionality, no internet required
- **Multiple TTS Engines**: Support for Coqui TTS, eSpeak, eSpeak-NG, MaryTTS, pyttsx3, and Festival
- **Auto-Detection**: Automatic detection and management of available TTS engines
- **Streaming & Batch**: Both real-time streaming and batch synthesis capabilities
- **Multi-language Support**: Extensive language and voice support across backends

## Repository Structure

### Core Components

#### `/TTS/` - Coqui TTS Core Library
The foundation TTS library providing neural TTS models:
- **`/tts/`**: Core TTS models and implementations
  - `models/`: Model implementations (Tacotron, Tacotron2, GlowTTS, VITS, etc.)
  - `configs/`: Configuration classes for different models
  - `datasets/`: Dataset handling and formatters
  - `layers/`: Neural network layers and components
  - `utils/`: Utility functions for text processing, synthesis, etc.
- **`/vocoder/`**: Neural vocoder implementations
  - `models/`: Vocoder models (HiFiGAN, MelGAN, WaveRNN, etc.)
  - `configs/`: Vocoder configuration classes
  - `layers/`: Vocoder-specific neural layers
- **`/encoder/`**: Speaker encoder for multi-speaker TTS
- **`/server/`**: Built-in TTS server implementation
- **`/bin/`**: Command-line tools and scripts

#### `/multi_tts_api/` - Unified TTS API
The main API application providing unified access to all TTS backends:
- **`api.py`**: FastAPI application with REST endpoints
- **`backend_manager.py`**: Backend orchestration and management
- **`backends/`**: Individual TTS backend implementations
  - `base.py`: Abstract base class for all backends
  - `coqui_tts.py`: Coqui TTS integration
  - `espeak.py`: eSpeak backend
  - `espeak_ng.py`: eSpeak-NG backend
  - `festival.py`: Festival TTS backend
  - `marytts.py`: MaryTTS backend
  - `pyttsx3_backend.py`: pyttsx3 wrapper backend
- **`run_server.py`**: Server startup script
- **`test_api.py`**: API test suite

### Training & Examples

#### `/recipes/`
Pre-configured training recipes for various datasets and models:
- `ljspeech/`: LJSpeech dataset recipes
- `vctk/`: VCTK multi-speaker dataset recipes
- `multilingual/`: Multilingual TTS recipes
- Each recipe includes model-specific training scripts

#### `/notebooks/`
Jupyter notebooks for tutorials and analysis:
- Tutorial notebooks for using pretrained models
- Dataset analysis tools
- Model attention visualization

### Testing & Quality

#### `/tests/`
Comprehensive test suite:
- `tts_tests/`: TTS model tests
- `vocoder_tests/`: Vocoder model tests
- `text_tests/`: Text processing tests
- `inference_tests/`: Inference and synthesis tests
- `data_tests/`: Dataset and data loader tests

### Documentation

#### `/docs/`
Sphinx documentation source:
- Installation guides
- Training tutorials
- Model implementation guides
- Dataset formatting instructions

## Technology Stack

### Core Dependencies

#### Deep Learning Framework
- **PyTorch**: >= 1.7 (primary deep learning framework)
- **torchaudio**: Audio processing with PyTorch
- **NumPy**: 1.21.6-1.22.4 (numerical computing)
- **SciPy**: >= 1.4.0 (scientific computing)

#### Audio Processing
- **librosa**: 0.8.0 (audio analysis)
- **soundfile**: Audio file I/O
- **numba**: 0.55.1-0.55.2 (JIT compilation for audio processing)
- **pydub**: 0.25.1 (audio manipulation)

#### API Framework
- **FastAPI**: 0.104.1 (modern async web framework)
- **uvicorn**: 0.24.0 (ASGI server)
- **pydantic**: 2.4.2 (data validation)

#### TTS-Specific
- **Coqui Trainer**: Training framework for TTS models
- **coqpit**: >= 0.0.16 (configuration management)
- **gruut**: 2.2.3 (grapheme-to-phoneme conversion)

#### Language Support
- **jieba**, **pypinyin**: Chinese text processing
- **mecab-python3**, **unidic-lite**: Japanese text processing
- **jamo**, **g2pkk**: Korean text processing
- **anyascii**: Unicode transliteration

## API Endpoints

### Core Endpoints

1. **GET /backends** - List all available TTS backends
2. **GET /backends/{backend_id}** - Get specific backend information
3. **POST /synthesize** - Synthesize speech with specified backend
4. **POST /synthesize/stream** - Stream synthesis for real-time output
5. **POST /synthesize/batch** - Batch synthesis for multiple texts

### Request Parameters
- `text`: Input text to synthesize
- `backend`: TTS backend to use
- `language`: Target language code
- `voice`: Voice/speaker selection
- `speed`: Speech rate adjustment
- `pitch`: Pitch adjustment
- `format`: Output audio format (wav, mp3, etc.)

## Deployment

### Docker Support
- Multi-stage Dockerfile with NVIDIA GPU support
- Includes all TTS backend system dependencies
- Configurable entrypoint for different services
- Docker Compose configuration for multi-service deployment

### CapRover Support
- One-click deployment configuration
- Captain definition for automated builds
- Environment variable configuration

### Environment Variables
- `TTS_MODEL_NAME`: Default TTS model for Coqui
- `TTS_SERVER_PORT`: Port for TTS server (default: 5002)
- `MULTI_TTS_HOST`: API host binding (default: 0.0.0.0)
- `MULTI_TTS_PORT`: API port (default: 8000)

## Development Workflow

### Setup Commands
```bash
# Install dependencies
pip install -r requirements.txt
cd multi_tts_api && pip install -r requirements.txt

# Run tests
pytest tests/

# Start API server
python -m uvicorn multi_tts_api.api:app --host 0.0.0.0 --port 8000

# Start Coqui TTS server
tts-server --model_name tts_models/en/ljspeech/tacotron2-DDC
```

### Code Quality Tools
- **Black**: Code formatting (line-length: 120)
- **isort**: Import sorting
- **flake8**: Linting (max-line-length: 120)
- **pytest**: Testing framework

## Recent Updates

### Latest Features (as of current branch)
1. **Multi-Backend TTS API**: Unified interface for multiple TTS engines
2. **Docker/CapRover Support**: Enhanced deployment options
3. **Improved CI/CD**: Fixed setup.py import issues
4. **Enhanced Documentation**: Updated README with multi-backend focus

## Architecture Decisions

### Design Patterns
- **Abstract Base Classes**: Backend implementations inherit from base class
- **Factory Pattern**: Backend manager dynamically loads available engines
- **Async/Await**: FastAPI leverages async for concurrent requests
- **Modular Architecture**: Clean separation between TTS engines and API layer

### Performance Considerations
- Lazy loading of TTS models to reduce startup time
- Caching of synthesized audio when appropriate
- Streaming support for real-time applications
- Batch processing for efficiency

## Supported TTS Backends

| Backend | Quality | Speed | Languages | Use Case |
|---------|---------|-------|-----------|----------|
| **Coqui TTS** | Excellent | Medium | 20+ | High-quality neural synthesis |
| **eSpeak** | Fair | Very Fast | 50+ | Lightweight, resource-constrained |
| **eSpeak-NG** | Good | Very Fast | 100+ | Improved eSpeak, broader language support |
| **MaryTTS** | Good | Medium | Multiple | Customizable, research-oriented |
| **pyttsx3** | Varies | Fast | Platform-dependent | Cross-platform compatibility |
| **Festival** | Good | Medium | Multiple | Highly configurable synthesis |

## Model Architectures

### TTS Models
- **Tacotron/Tacotron2**: Sequence-to-sequence with attention
- **GlowTTS**: Flow-based generative model
- **VITS**: Variational Inference with adversarial learning
- **FastSpeech/FastPitch**: Non-autoregressive models
- **AlignTTS**: Efficient alignment-based synthesis

### Vocoder Models
- **HiFiGAN**: High-fidelity GAN vocoder
- **MelGAN/MultiBand-MelGAN**: Efficient GAN vocoders
- **WaveRNN**: Autoregressive neural vocoder
- **WaveGrad**: Diffusion-based vocoder
- **UnivNet**: Universal neural vocoder

## Testing Strategy

### Test Coverage
- Unit tests for individual components
- Integration tests for API endpoints
- Model training tests (reduced epochs)
- Audio quality validation tests
- Multi-backend compatibility tests

### Continuous Integration
- Automated testing on pull requests
- Docker build verification
- Dependency compatibility checks

## Future Roadmap Considerations

### Potential Enhancements
- Additional TTS backend integrations
- WebSocket support for real-time streaming
- Audio post-processing effects
- Voice cloning capabilities expansion
- Cloud deployment templates (AWS, GCP, Azure)
- GraphQL API alternative
- Kubernetes Helm charts
- Monitoring and analytics dashboard

## Important Notes

### Security Considerations
- Input text sanitization
- Rate limiting for API endpoints
- Authentication/authorization options
- Secure model storage and access

### Performance Optimization
- Model quantization options
- GPU acceleration configuration
- Memory management for large models
- Request queuing and prioritization

### Licensing
- Core project uses Mozilla Public License 2.0 (Coqui TTS)
- Individual backends have varying licenses
- Check specific backend documentation for license requirements