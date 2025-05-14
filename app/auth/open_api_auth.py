from fastapi import FastAPI

from fastapi.openapi.utils import get_openapi
from app.config import env

# 1) Crie uma função que injeta o BearerAuth no schema
def add_global_bearer_auth(app: FastAPI, scheme_name: str = "BearerAuth"):
    def custom_openapi():
        # reaproveita o schema gerado automaticamente
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="GEE‑Integrator‑API",
            version="0.1.0",
            description="API para integração com Google Earth Engine",
            routes=app.routes,
        )

        # --- securitySchemes -----------------------------------------------
        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes[scheme_name] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # só para fins de documentação
        }

        # --- aplica o requisito de segurança a todos os caminhos ------------
        WHITELIST = {("/", "get"), ("/healthz", "get")}  # rotas públicas
        for path, methods in openapi_schema["paths"].items():
            for method, op in methods.items():
                if (path, method) in WHITELIST:
                    continue  # deixa público
                op.setdefault("security", [{scheme_name: []}])

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    # substitui o gerador padrão
    app.openapi = custom_openapi
