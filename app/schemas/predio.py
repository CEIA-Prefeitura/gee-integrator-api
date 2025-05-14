from pydantic import BaseModel
from typing import Optional


class PredioListItem(BaseModel):
    id: int
    latitude_1: Optional[float]
    longitude_: Optional[float]
    area_in__1: Optional[float]
    confiden_1: Optional[float]
    full_plus1: Optional[str]
    area_km2: Optional[float]
    area_mt: Optional[float]

    class Config:
        from_attributes = True


class PredioRead(PredioListItem):
    geom: Optional[str]  # WKT string (ex: 'MULTIPOLYGON(((...)))')

