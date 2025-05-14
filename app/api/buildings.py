# -*- coding: utf-8 -*-
"""

Endpoints para a coleção Google **Open Buildings 2.5‑D Temporal**.

Gera tiles PNG (XYZ) das bandas `building_presence` ou `building_height`,
por ano, com cache em Valkey (tanto da imagem quanto da URL GEE).

Parâmetros
==========
* `x`, `y`, `z`→ coordenadas XYZ do tile
* `year` → ano desejado (default = ano corrente)
* `band`→ `presence`(padrão) ou `height`

Zoom válido → 10 ≤ z ≤ 18
Cache URL GEE→ `settings.LIFESPAN_URL` (horas)

RoleAPIRouter é usado para proteger as rotas; aplique decorators de role onde
for necessário.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from enum import Enum
from typing import Final

import aiohttp
import ee
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.auth.role_route import RoleAPIRouter
from app.config import logger, settings
from app.errors import generate_error_image
from app.tile import tile2goehashBBOX
from app.utils.cache import getCacheUrl
from app.utils.capabilities import CAPABILITIES

# ----------------------------------------------------------------------------
# Configurações gerais
# ----------------------------------------------------------------------------
router: APIRouter = RoleAPIRouter()

COLLECTION: Final[str] = "GOOGLE/Research/open-buildings-temporal/v1"
MIN_ZOOM: Final[int] = 10
MAX_ZOOM: Final[int] = 18
CACHE_TTL_HOURS: Final[int] = settings.LIFESPAN_URL  # horas


class Band(str, Enum):
    """Bandas disponíveis na coleção."""

    presence = "presence"  # building_presence
    height = "height"      # building_height


# Paletas de cores e parâmetros de visualização (replicam as figuras enviadas).
BAND_VISPARAMS: Final[dict[Band, dict[str, int | list[str]]]] = {
    Band.height: {
        "bands": ["building_height"],
        "min": 0,
        "max": 30,
        "palette": [
            "002873",  # azul escuro
            "1e6caf",  # azul médio
            "39a7b4",  # turquesa
            "7ecf4c",  # verde
            "ffe971",  # amarelo
            "ff7c39",  # laranja
            "ff0000",  # vermelho
        ],
    },
    Band.presence: {
        "bands": ["building_presence"],
        "min": 0,
        "max": 1,
        "palette": [
            "000000",  # sem edifício
            "2446c0",  # azul
            "2ca02c",  # verde
            "ffdd57",  # amarelo claro
        ],
    },
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
async def _fetch_png(url: str) -> bytes:
    """Faz download do tile PNG remoto."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise HTTPException(resp.status, "Imagem não encontrada na API externa")
            return await resp.read()


def _zoom_valido(z: int) -> bool:
    return MIN_ZOOM <= z <= MAX_ZOOM


def _ano_valido(year: int) -> bool:
    meta = next((c for c in CAPABILITIES["collections"] if c["name"] == "open_buildings"), None)
    return not meta or year in meta.get("year", [])

# ----------------------------------------------------------------------------
# Endpoint
# ----------------------------------------------------------------------------
@router.get("/{x}/{y}/{z}", name="Open Buildings PNG")
async def get_open_buildings_png(
    request: Request,
    x: int,
    y: int,
    z: int,
    year: int = datetime.now().year,
    band: Band = Band.presence,
):
    """Retorna o tile PNG (XYZ) da banda escolhida para o ano especificado."""

    # ---------- Validações rápidas -----------------------------------------
    if not _zoom_valido(z):
        return FileResponse("data/maxminzoom.png", media_type="image/png")

    if not _ano_valido(year):
        logger.debug("Ano inválido recebido: %s", year)
        return FileResponse("data/notfound.png", media_type="image/png")

    # ---------- Chaves de cache --------------------------------------------
    geohash, bbox = tile2goehashBBOX(x, y, z)
    path_cache = f"open_buildings_{band}_{year}/{geohash}"
    file_cache = f"{path_cache}/{z}/{x}_{y}.png"

    # PNG já em cache
    cached_png = request.app.state.valkey.get(file_cache)
    if cached_png:
        return StreamingResponse(io.BytesIO(cached_png), media_type="image/png")

    # ---------- URL GEE -----------------------------------------------------
    url_info = getCacheUrl(request.app.state.valkey.get(path_cache))
    url_expired = (
        url_info is None or datetime.now() - url_info["date"] > timedelta(hours=CACHE_TTL_HOURS)
    )

    if url_expired:
        try:
            geom = ee.Geometry.BBox(bbox["w"], bbox["s"], bbox["e"], bbox["n"])

            collection = (
                ee.ImageCollection(COLLECTION)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .filterBounds(geom)
            )

            if collection.size().getInfo() == 0:
                logger.debug("Sem dados do Open Buildings para %s", year)
                return FileResponse("data/notfound.png", media_type="image/png")

            image = collection.mosaic().select(*BAND_VISPARAMS[band]["bands"])

            vis = {k: v for k, v in BAND_VISPARAMS[band].items() if k != "bands"}

            # Converte min/max numéricos para string, exigência do SDK GEE.
            for key in ("min", "max"):
                if isinstance(vis.get(key), (int, float)):
                    vis[key] = str(vis[key])

            # Converte lista de paleta em string separada por vírgulas.
            if isinstance(vis.get("palette"), list):
                vis["palette"] = ",".join(vis["palette"])

            map_id = ee.data.getMapId({"image": image, **vis})
            tile_url = map_id["tile_fetcher"].url_format

            request.app.state.valkey.set(path_cache, f"{tile_url}, {datetime.now()}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("%s | %s", file_cache, exc)
            return StreamingResponse(generate_error_image(f"Erro: {exc}"), media_type="image/png")
    else:
        tile_url = url_info["url"]

    # ---------- Download do PNG e grava no cache ---------------------------
    try:
        png = await _fetch_png(tile_url.format(x=x, y=y, z=z))
        request.app.state.valkey.set(file_cache, png)
    except HTTPException as exc:
        logger.exception("%s %s", file_cache, exc.detail)
        return StreamingResponse(generate_error_image(f"Erro: {exc.detail}"), media_type="image/png")

    logger.info("Tile gerado %s", file_cache)
    return StreamingResponse(io.BytesIO(png), media_type="image/png")
