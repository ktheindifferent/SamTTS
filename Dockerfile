ARG BASE=nvcr.io/nvidia/pytorch:22.03-py3
FROM ${BASE}

# Install system dependencies including additional TTS backends
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make python3 python3-dev python3-pip python3-venv python3-wheel \
    espeak espeak-ng libsndfile1-dev \
    festival festvox-kallpc16k \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install llvmlite --ignore-installed

# Create and activate virtual env
ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install -U pip setuptools wheel

WORKDIR /app
COPY requirements.txt requirements.dev.txt requirements.notebooks.txt /app/
RUN ["/bin/bash", "-c", "pip install -r <(cat requirements.txt requirements.dev.txt requirements.notebooks.txt)"]

# Copy multi_tts_api requirements and install
COPY multi_tts_api/requirements.txt /app/multi_tts_api_requirements.txt
RUN pip install -r /app/multi_tts_api_requirements.txt

# Copy source code
COPY . /app/
RUN make install

# Expose ports
EXPOSE 5002 8000

# Create entrypoint script to support multiple services
RUN echo '#!/bin/bash\n\
if [ "$1" = "tts-server" ]; then\n\
  exec tts-server --model_name "${TTS_MODEL_NAME:-tts_models/en/ljspeech/tacotron2-DDC}" --port "${TTS_SERVER_PORT:-5002}"\n\
elif [ "$1" = "multi-tts-api" ]; then\n\
  exec python /app/multi_tts_api/run_server.py --host "${MULTI_TTS_HOST:-0.0.0.0}" --port "${MULTI_TTS_PORT:-8000}"\n\
else\n\
  exec tts "$@"\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["tts-server"]
