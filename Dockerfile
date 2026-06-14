# Image for the public DensityGen web demo.
# Descriptor scoring runs by default; the "real simulation" toggle uses a real
# ML interatomic potential. We bundle CHGNet (ungated, ships its own weights, no
# HuggingFace access or network) so real energies work on the box with no
# secrets. fairchem/UMA stay out (gated + heavy); the Replicate path still works
# if DENSITYGEN_UMA_MODEL + REPLICATE_API_TOKEN are set.
FROM python:3.12-slim

WORKDIR /app

# Install the package plus the web/remote-simulation dependencies.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[web]"

# Real ML-potential backend (CPU). Install the CPU-only torch wheel first from
# the dedicated index so we don't pull multi-GB CUDA wheels, then CHGNet.
# REASON: CHGNet is the ungated engine get_backend() falls back to; without it
# the hosted "real simulation" has no backend and 503s.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
 && pip install --no-cache-dir chgnet

# The web app lives outside the package (repo-level web/).
COPY web ./web

EXPOSE 7860
# Shell form so ${PORT} is expanded. fly injects PORT=8080; HF Spaces routes to
# 7860 (app_port). Default 7860 covers HF when PORT is unset. Works for both.
CMD uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-7860}
