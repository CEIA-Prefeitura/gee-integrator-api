from .api import layers, timeseries


def created_routes(app):

    app.include_router(layers.router, prefix="/api/layers", tags=["Camadas"])
    app.include_router(timeseries.router, prefix="/api/timeseries", tags=["Series temporais Sentinel e Landsat"])

    return app
