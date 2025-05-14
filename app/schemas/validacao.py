
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import StatusEdificacao


# -------- Validacao -------- #
class ValidacaoBase(BaseModel):
    nome: str
    bairro_id: int
    data_inicio: datetime
    data_fim: datetime
    descricao: Optional[str] = None


class ValidacaoCreate(ValidacaoBase):
    pass


class ValidacaoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    bairro_id: Optional[int] = None


class ValidacaoRead(ValidacaoBase):
    id: int
    usuario: str
    data_insercao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True


# -------- Inspecao -------- #
class InspecaoBase(BaseModel):
    ano: int
    edificacao_confirmada: StatusEdificacao = Field(
        default=StatusEdificacao.PENDENTE, description="PENDENTE ou EDIFICACAO_CONFIRMADA"
    )


class InspecaoCreate(InspecaoBase):
    pass


class InspecaoUpdate(BaseModel):
    edificacao_confirmada: Optional[StatusEdificacao] = None


class InspecaoRead(InspecaoBase):
    id: int
    datetime_inserida: datetime
    usuario: str

    class Config:
        from_attributes = True
