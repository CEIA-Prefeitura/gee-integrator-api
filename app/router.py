from .api import layers, timeseries, planet, buildings, buildings_ts


def created_routes(app):
    app.include_router(buildings.router, prefix="/api/buildings", tags=["Open Building Layer"])
    app.include_router(buildings_ts.router, prefix="/api/buildings-ts", tags=["Open Building Timeseries"])
    app.include_router(layers.router, prefix="/api/layers", tags=["Layers"])
    app.include_router(timeseries.router, prefix="/api/timeseries", tags=["Series temporais Sentinel e Landsat"])
    app.include_router(planet.router, prefix="/api/planet", tags=["Rede Mais - Planet GEOServices Proxy"])
    return app
