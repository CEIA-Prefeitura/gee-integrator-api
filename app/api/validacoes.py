# app/api/validacoes.py
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.role_route import RoleAPIRouter          # já existente
from app.middleware.sso_keycloack import get_username     # devolve username / roles
from app.database import get_async_session
from app.models import Validacao, Inspecao
from app.schemas.validacao import (
    ValidacaoCreate, ValidacaoRead, ValidacaoUpdate,
    InspecaoCreate,  InspecaoRead,  InspecaoUpdate,
)

router = RoleAPIRouter()

@router.post(
    "",
    response_model=ValidacaoRead,
    status_code=status.HTTP_201_CREATED,
    roles=["gee-integrator-api.user_access"],
)
async def create_validacao(
    payload: ValidacaoCreate,
    db: AsyncSession = Depends(get_async_session),
    username: str = Depends(get_username),
):
    obj = Validacao(**payload.model_dump(), usuario=username)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "",
    response_model=list[ValidacaoRead],
    roles=["gee-integrator-api.user_access"],
)
async def list_validacoes(
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.scalars(select(Validacao).order_by(Validacao.id.desc()))
    return result.all()


@router.get(
    "/{validacao_id}",
    response_model=ValidacaoRead,
    roles=["gee-integrator-api.user_access"],
)
async def get_validacao(
    validacao_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    obj = await db.get(Validacao, validacao_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validação não encontrada")
    return obj


@router.patch(
    "/{validacao_id}",
    response_model=ValidacaoRead,
    roles=["gee-integrator-api.user_access"],
)
async def update_validacao(
    validacao_id: int,
    payload: ValidacaoUpdate,
    db: AsyncSession = Depends(get_async_session),
    username: str = Depends(get_username),
):
    values = payload.model_dump(exclude_unset=True)
    values["data_atualizacao"] = datetime.now(timezone.utc)
    values["usuario"] = username
    stmt = (
        update(Validacao)
        .where(Validacao.id == validacao_id)
        .values(**values)
        .returning(Validacao)
    )
    result = await db.scalar(stmt)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validação não encontrada")
    await db.commit()
    return result


@router.delete(
    "/{validacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    roles=["gee-integrator-api.user_access"],
)
async def delete_validacao(
    validacao_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    deleted = await db.scalar(
        delete(Validacao).where(Validacao.id == validacao_id).returning(Validacao.id)
    )
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validação não encontrada")
    await db.commit()
    return None


@router.post(
    "/{validacao_id}/inspecoes",
    response_model=InspecaoRead,
    status_code=status.HTTP_201_CREATED,
    roles=["gee-integrator-api.user_access"],
)
async def create_inspecao(
    validacao_id: int,
    payload: InspecaoCreate,
    db: AsyncSession = Depends(get_async_session),
    username: str = Depends(get_username),
):
    # valida existência da validação
    if not await db.get(Validacao, validacao_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Validação não encontrada")

    obj = Inspecao(
        **payload.model_dump(),
        validacao_id=validacao_id,
        usuario=username,
        datetime_inserida=datetime.now(timezone.utc),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/{validacao_id}/inspecoes",
    response_model=list[InspecaoRead],
    roles=["gee-integrator-api.user_access"],
)
async def list_inspecoes(
    validacao_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.scalars(
        select(Inspecao).where(Inspecao.validacao_id == validacao_id)
    )
    return result.all()


@router.patch(
    "/{validacao_id}/inspecoes/{inspecao_id}",
    response_model=InspecaoRead,
    roles=["gee-integrator-api.user_access"],
)
async def update_inspecao(
    validacao_id: int,
    inspecao_id: int,
    payload: InspecaoUpdate,
    db: AsyncSession = Depends(get_async_session),
    username: str = Depends(get_username),
):
    values = payload.model_dump(exclude_unset=True)
    values["usuario"] = username
    stmt = (
        update(Inspecao)
        .where(
            Inspecao.id == inspecao_id,
            Inspecao.validacao_id == validacao_id,
        )
        .values(**values)
        .returning(Inspecao)
    )
    result = await db.scalar(stmt)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspeção não encontrada")
    await db.commit()
    return result


@router.delete(
    "/{validacao_id}/inspecoes/{inspecao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    roles=["gee-integrator-api.user_access"],
)
async def delete_inspecao(
    validacao_id: int,
    inspecao_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    deleted = await db.scalar(
        delete(Inspecao).where(
            Inspecao.id == inspecao_id,
            Inspecao.validacao_id == validacao_id,
        ).returning(Inspecao.id)
    )
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspeção não encontrada")
    await db.commit()
    return None
