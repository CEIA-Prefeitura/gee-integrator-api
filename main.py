import typing
from contextlib import asynccontextmanager

import ee
import orjson
import valkey
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account

from app.config import settings, logger, start_logger, env
from app.router import created_routes
from app.utils.cors import origin_regex, allow_origins
from app.middleware.sso_keycloack import KeycloakAuthMiddleware
from app.middleware.exception_handler import register_exception_handlers
from app.auth.open_api_auth import add_global_bearer_auth



class ORJSONResponse(JSONResponse):
    media_type = "application/json"
    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_logger()
    try:
        service_account_file = settings.GEE_SERVICE_ACCOUNT_FILE
        logger.debug(f"Initializing service account {service_account_file}")
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/earthengine.readonly"],
        )
        ee.Initialize(credentials)
        print("GEE Initialized successfully.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to initialize GEE")

    app.state.valkey = valkey.Valkey(host=env.get("VALKEY_HOST", 'valkey'), port=env.get("VALKEY_PORT", 6379))
    yield
    app.state.valkey.close()

app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)
add_global_bearer_auth(app)

# Configurações CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    allow_origin_regex=origin_regex,
    expose_headers=["X-Response-Time"],
    max_age=3600,
)

app.add_middleware(KeycloakAuthMiddleware)
register_exception_handlers(app)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo ao GEE-Integrator-API"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/healthz", tags=["Infra"])
def health_check():
    return {"status": "ok"}

app = created_routes(app)
