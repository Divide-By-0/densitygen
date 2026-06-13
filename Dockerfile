# Lightweight image for the public DensityGen web demo.
# REASON: the web path runs descriptor scoring by default and can optionally call
# a remote Replicate UMA model. We install ASE + replicate for that remote path,
# but deliberately avoid local torch/fairchem/chgnet to keep the image small.
FROM python:3.12-slim

WORKDIR /app

# Install the package plus the web/remote-simulation dependencies.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[web]"

# The web app lives outside the package (repo-level web/).
COPY web ./web

EXPOSE 7860
# Shell form so ${PORT} is expanded. fly injects PORT=8080; HF Spaces routes to
# 7860 (app_port). Default 7860 covers HF when PORT is unset. Works for both.
CMD uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-7860}
