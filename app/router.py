from .api import layers, timeseries, planet, buildings


def created_routes(app):
    app.include_router(buildings.router, prefix="/api/buildings", tags=["Open Building"])
    app.include_router(layers.router, prefix="/api/layers", tags=["Layers"])
    app.include_router(timeseries.router, prefix="/api/timeseries", tags=["Timeseries Sentinel and Landsat"])
    app.include_router(planet.router, prefix="/api/planet", tags=["Planet GeoServices Proxy"])
    return app
