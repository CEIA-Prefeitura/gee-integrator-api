FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv


ENV TILES_ENV='production'
    
LABEL maintainer="Tharles de Sousa Andrade <irtharles@gmail.com>"

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential git nano && \
    uv pip install --system --no-cache-dir -r requirements.txt


