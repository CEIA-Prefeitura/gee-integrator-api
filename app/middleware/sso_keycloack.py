from time import time
from venv import logger

import aiohttp
from fastapi import Depends, Request, HTTPException
from fastapi import status
from jose import jwt, jwk, JWTError
from jose.constants import ALGORITHMS
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import env

ISSUER   = f"{env.get('SSO_SERVER_URL').rstrip('/')}/realms/{env.get('SSO_REALM')}"
AUDIENCE = env.get("SSO_CLIENT_ID")
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"
CACHE_TTL = 60 * 10
WHITELIST_PATHS = [
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
    "/auth",
    "/healthz"
]
# ------------------------------------------------------------------ #
# JWK cache (kid ➜ jose.jwk.Key) with automatic background refreshes #
# ------------------------------------------------------------------ #
_jwks_cache: dict[str, tuple[float, dict]] = {}

async def _get_key(kid: str):
    # still valid?
    item = _jwks_cache.get(kid)
    if item and time() - item[0] < CACHE_TTL:
        return item[1]

    # refresh whole JWKS once; keep only the key we need in RAM
    async with aiohttp.ClientSession() as s:
        async with s.get(JWKS_URL, timeout=5) as r:
            keys = (await r.json())["keys"]

    for raw in keys:
        _jwks_cache[raw["kid"]] = (time(), jwk.construct(raw, ALGORITHMS.RS256))

    if kid not in _jwks_cache:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "kid não encontrado")
    return _jwks_cache[kid][1]

def _extract_roles(payload: dict) -> list[str]:
    roles: list[str] = payload.get("realm_access", {}).get("roles", [])
    for client, data in payload.get("resource_access", {}).items():
        roles.extend(f"{client}.{r}" for r in data.get("roles", []))
    return roles

class KeycloakAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in WHITELIST_PATHS:
            return await call_next(request)
        # paths sem autenticação
        if request.url.path in WHITELIST_PATHS:
            return await call_next(request)

        token = _extract_token(request)
        try:
            header  = jwt.get_unverified_header(token)
            key     = await _get_key(header["kid"])
            payload = jwt.decode(
                token, key, algorithms=[ALGORITHMS.RS256],
                audience=AUDIENCE, issuer=ISSUER,
            )
        except JWTError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                f"Token inválido: {exc}") from exc

        # coloca no request.state para ser reutilizado pelos endpoints/deps
        request.state.user  = payload
        request.state.roles = _extract_roles(payload)
        return await call_next(request)

# helpers --------------------------------------------------------------------
def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    logger.debug(auth)
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    # fallback: ?authToken=t
    if token := request.query_params.get("authToken"):
        return token
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token não informado")

def get_current_user(request: Request) -> dict:
    """
    Devolve o payload JWT validado.
    Lança 401 se o middleware não colocou nada no request.state.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(401, "Não autenticado")
    return user

def get_username(user: dict = Depends(get_current_user)) -> str:
    return user.get("preferred_username") or user.get("sub")