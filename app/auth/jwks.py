import requests
from app.config import env

JWKS_URL = f"{env.get('SSO_SERVER_URL').rstrip('/')}/realms/{env.get('SSO_REALM')}/protocol/openid-connect/certs"

def get_jwk_by_kid(kid: str):
    response = requests.get(JWKS_URL)
    jwks = response.json()["keys"]
    for key in jwks:
        if key["kid"] == kid:
            return key
    raise ValueError(f"Chave JWK com kid={kid} não encontrada")
