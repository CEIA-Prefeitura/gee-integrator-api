import ee
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from scipy.signal import savgol_filter
from datetime import datetime
from app.auth.role_route import RoleAPIRouter

router: APIRouter = RoleAPIRouter()

@router.get("/{lat}/{lon}")
def timeseries_open_buildings(
    lat: float,
    lon: float,
    banda: str = Query("height", enum=["presence", "height"]),
    data_inicio: str = Query("2015-07-01"),
    data_fim: str = Query(None)

):
    if not data_fim:
        data_fim = datetime.now().strftime('%Y-%m-%d')
    try:
        point = ee.Geometry.Point([lon, lat])
        collection = ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1") \
            .filterDate(data_inicio, data_fim) \
            .filterBounds(point)

        banda_gee = {
            "presence": "building_presence",
            "height": "building_height"
        }[banda]

        def extract_band_timeseries(image):
            date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
            value = image.select(banda_gee).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=10
            ).get(banda_gee)
            return ee.Feature(None, {"date": date, banda: value})

        series = collection.map(extract_band_timeseries).filter(
            ee.Filter.notNull([banda])
        )

        data = series.reduceColumns(
            ee.Reducer.toList(2), ['date', banda]
        ).get('list').getInfo()

        if not data:
            return JSONResponse(content=[], status_code=204)

        dates, values = zip(*data)
        df = pd.DataFrame({'date': dates, banda: values})
        df = df.groupby('date').mean().reset_index()

        def smooth(values, window_size=5, poly_order=2):
            if len(values) >= window_size:
                return savgol_filter(values, window_size, poly_order).tolist()
            return values

        values_raw = df[banda].tolist()
        values_smoothed = smooth(np.array(values_raw))

        return JSONResponse(content=[
            {
                "x": df['date'].tolist(),
                "y": values_raw,
                "type": "scatter",
                "mode": "markers",
                "name": f"{banda} (Original)"
            },
            {
                "x": df['date'].tolist(),
                "y": values_smoothed,
                "type": "scatter",
                "mode": "lines",
                "name": f"{banda} (Smoothed)"
            }
        ])

    except ee.EEException as e:
        raise HTTPException(status_code=500, detail=f"Earth Engine error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
