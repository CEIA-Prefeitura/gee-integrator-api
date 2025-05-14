import os
from collections import defaultdict
from typing import Any, Dict, List

import aiohttp
import xmltodict
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.auth.role_route import RoleAPIRouter
from app.config import logger, env

router = RoleAPIRouter()

def _get_nested(obj: Any, path: List[str], default=None):
    cur = obj
    for key in path:
        if cur is None or key not in cur:
            return default
        cur = cur[key]
    return cur

async def _get_env(var: str) -> str:
    value = getattr(env, var, None) or os.getenv(var)
    if not value:
        raise HTTPException(400, f"Variável de ambiente {var} não foi definida.")
    return value

@router.get("/capabilities", roles=["gee-integrator-api.user_access"])
async def planet_capabilities() -> Dict[str, List[Dict[str, str]]]:
    planet_url  = await _get_env("PLANET_WMS_URL")
    planet_auth = await _get_env("PLANET_AUTH_TOKEN")

    url = f"{planet_url}?SERVICE=WMS&REQUEST=GetCapabilities"
    headers = {
        "Authorization": f"Basic {planet_auth}",
        "User-Agent": "Mozilla/5.0 QGIS/33415/Linux",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status != 200:
                logger.error(f"GetCapabilities falhou ({r.status})")
                raise HTTPException(r.status, "Falha ao obter GetCapabilities")
            xml_text = await r.text()

    try:
        capabilities = xmltodict.parse(xml_text)
    except Exception as exc:
        logger.exception("Erro ao parsear XML")
        raise HTTPException(500, f"Parsing XML error: {exc}")

    layers = _get_nested(
        capabilities, ["WMS_Capabilities", "Capability", "Layer", "Layer"], []
    )

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for layer in layers:
        name = layer.get("Name", "")
        partes = name.split("_")
        if len(partes) < 5:
            continue

        year, month = partes[2:4]
        tipo = "_".join(partes[5:]) if len(partes) > 5 else partes[-1]
        iso_date = f"{year}-{month.zfill(2)}-01T23:59:59Z"

        grouped[tipo].append({"name": name, "date": iso_date})

    for tipo in grouped:
        grouped[tipo].sort(key=lambda x: x["date"])

    return grouped

@router.get("/proxy", roles=["gee-integrator-api.user_access"])
async def planet_proxy(request: Request) -> Response:
    planet_url  = await _get_env("PLANET_WMS_URL")
    planet_auth = await _get_env("PLANET_AUTH_TOKEN")

    if not (query_string := request.url.query):
        raise HTTPException(400, "Query string é obrigatória")

    proxied_url = f"{planet_url}?{query_string}"
    headers = {
        "Authorization": f"Basic {planet_auth}",
        "User-Agent": "Mozilla/5.0 QGIS/32804/Windows 10",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(proxied_url, headers=headers) as r:
            content = await r.read()
            if r.status != 200:
                logger.error(f"Proxy Planet retornou {r.status}")
                raise HTTPException(r.status, "Erro ao buscar dados no Planet")

            media_type = r.headers.get("Content-Type", "application/octet-stream")
            return Response(content, media_type=media_type)
