from .api import layers, timeseries, planet, buildings, buildings_ts, predios, validacoes


def created_routes(app):
    app.include_router(buildings.router, prefix="/api/buildings", tags=["Buildings Layer"])
    app.include_router(buildings_ts.router, prefix="/api/buildings-ts", tags=["Buildings Timeseries"])
    app.include_router(layers.router, prefix="/api/layers", tags=["Layers"])
    app.include_router(timeseries.router, prefix="/api/timeseries", tags=["Series temporais Sentinel e Landsat"])
    app.include_router(planet.router, prefix="/api/planet", tags=["Planet Geoservices Proxy"])
    app.include_router(predios.router, prefix="/api/predios", tags=["Predios"])
    app.include_router(validacoes.router, prefix="/api/validacoes", tags=["Validacoes & Inspecoes"])
    return app
