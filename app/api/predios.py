from fastapi import Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_route import RoleAPIRouter
from app.database import get_async_session
from app.models import Predio
from app.schemas.predio import PredioRead, PredioListItem

router = RoleAPIRouter()

async def fetch_predios(db: AsyncSession) -> list[PredioListItem]:
    stmt = select(
        Predio.id,
        Predio.latitude_1,
        Predio.longitude_,
        Predio.area_in__1,
        Predio.confiden_1,
        Predio.full_plus1,
        Predio.area_km2,
        Predio.area_mt,
    ).order_by(Predio.id.desc())

    result = await db.execute(stmt)
    return result.all()


@router.get("", response_model=list[PredioListItem], roles=["gee-integrator-api.user_access"])
async def list_predios(
    db: AsyncSession = Depends(get_async_session),
):
    return await fetch_predios(db)


@router.get(
    "/{predio_id}",
    response_model=PredioRead,
    roles=["gee-integrator-api.user_access"],
)
async def get_predio(
    predio_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    stmt = select(
        Predio.id,
        func.ST_AsText(Predio.geom).label("geom"),
        Predio.latitude_1,
        Predio.longitude_,
        Predio.area_in__1,
        Predio.confiden_1,
        Predio.full_plus1,
        Predio.area_km2,
        Predio.area_mt,
    ).where(Predio.id == predio_id)

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Prédio não encontrado")

    return dict(row._mapping)
