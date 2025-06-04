# ===========================
# 🏗️ Etapa 1: Builder
# ===========================
FROM python:3.12-slim-bookworm AS builder

# 🔧 Copia o binário do 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 📦 Build arguments
ARG TILES_ENV=production
ENV TILES_ENV=${TILES_ENV}

# 📁 Diretório de trabalho
WORKDIR /app

# 🧱 Instala dependências básicas
RUN apt-get update && apt-get install --no-install-recommends -y \
      build-essential curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 📂 Copia código e requisitos
COPY ./tiles ./tiles
COPY requirements.txt ./

# 📦 Instala dependências com uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# ===========================
# 🚀 Etapa 2: Imagem Final
# ===========================
FROM python:3.12-slim-bookworm

# 🔧 Copia binário e dependências da imagem builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

ARG TILES_ENV=production
ENV TILES_ENV=${TILES_ENV}
WORKDIR /app/tiles

# 👤 Usuário não-root
RUN addgroup --system tilesgroup && adduser --system --ingroup tilesgroup tilesuser && \
    chown -R tilesuser:tilesgroup /app

USER tilesuser

EXPOSE 8083

# 🚀 Execução da aplicação
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8083", "-w", "4", "-t", "0", "main:app"]
