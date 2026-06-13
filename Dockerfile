# Lightweight image for the public DensityGen web demo.
# REASON: the web path runs the *descriptor* scorer only (instant, abuse-safe),
# so we deliberately do NOT install torch/fairchem/chgnet here -- that keeps the
# image small (~150 MB) and cold-starts fast. Real UMA/CHGNet stays on the CLI.
FROM python:3.12-slim

WORKDIR /app

# Install the package (core deps: pydantic + numpy) plus the web server.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . fastapi "uvicorn[standard]"

# The web app lives outside the package (repo-level web/).
COPY web ./web

ENV PORT=8080
EXPOSE 8080
# Shell form so ${PORT} is expanded (fly injects PORT).
CMD uvicorn web.app:app --host 0.0.0.0 --port ${PORT}
