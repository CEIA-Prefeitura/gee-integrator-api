from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from geoalchemy2 import Geometry
from pydantic import BaseModel
from sqlalchemy import Column, Integer,  BigInteger, Float, Date, DateTime, ForeignKey, Enum as PgEnum, String, func

from sqlalchemy.orm import relationship

from .database import Base


class Layer(Base):
    __tablename__ = "layers"

    layer: str = Column(String(120), primary_key=True, index=True)
    url: str = Column(String(255), nullable=False)
    date: datetime = Column(DateTime(), nullable=False)


class LayerName(str, Enum):
    STATES = "states"
    BIOMES = "biomes"
    SICAR = "sicar"


class GEEConfig(BaseModel):
    service_account_file: str


class RegionRequest(BaseModel):
    coordinates: List[List[float]]


class FilterRequest(BaseModel):
    bioma: Optional[str] = None
    cd_bioma: Optional[int] = None


class StatusEdificacao(str, Enum):
    EDIFICACAO_CONFIRMADA = "EDIFICACAO_CONFIRMADA"
    PENDENTE              = "PENDENTE"

class Predio(Base):
    __tablename__ = "predios"

    id              = Column(Integer, primary_key=True, index=True)
    geom            = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4674))
    latitude_1      = Column(Float)
    longitude_      = Column(Float)
    area_in__1      = Column(Float)
    confiden_1      = Column(Float)
    full_plus1      = Column(String(254))
    area_km2        = Column(Float)
    area_mt         = Column(Float)


class Bairro(Base):
    __tablename__ = "bairros"

    objectid        = Column(BigInteger, primary_key=True, index=True)

    # geometria
    geom            = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4674))

    # colunas textuais / numéricas
    codigo          = Column("id",        String(12))
    tp_bai          = Column(String(5))
    nm_bai          = Column(String(80))
    id_sis          = Column(BigInteger)
    cd_err          = Column(BigInteger)
    nm              = Column(String(80))
    nm1             = Column(String(80))
    nm2             = Column(String(80))
    ql_bai          = Column(String(80))
    in_lei181       = Column(BigInteger)
    in_puama        = Column(BigInteger)
    id_re7          = Column(String(12))
    in_doc          = Column(BigInteger)
    x_coord         = Column(Float)
    y_coord         = Column(Float)
    pop_total       = Column(BigInteger)
    pop_masc        = Column(BigInteger)
    pop_fem         = Column(BigInteger)
    in_lei228       = Column(BigInteger)
    in_cond         = Column(BigInteger)
    id_mun          = Column(String(12))
    id_mzo          = Column(String(12))
    created_us      = Column(String(254))
    created_da      = Column(Date)
    last_edite      = Column(String(254))
    last_edi_1      = Column(Date)
    nm3             = Column(String(80))
    in_lei8618      = Column(BigInteger)
    shape_star      = Column(Float)
    shape_stle      = Column(Float)

    # relacionamento 1‑N com validações
    validacoes      = relationship("Validacao", back_populates="bairro")


# ────────────────────────────────────────────────────────────
# TABELAS NOVAS
# ────────────────────────────────────────────────────────────

class Validacao(Base):
    __tablename__ = "validacoes"

    id              = Column(Integer, primary_key=True, index=True)
    nome            = Column(String, nullable=False)
    descricao       = Column(String)
    bairro_id       = Column(
        BigInteger,
        ForeignKey("bairros.objectid", ondelete="CASCADE"),
        nullable=True
    )
    data_inicio     = Column(DateTime, nullable=False)
    data_fim        = Column(DateTime, nullable=False)
    usuario         = Column(String, nullable=False)
    data_insercao = Column(
        DateTime(timezone=True),  # TIMESTAMPTZ
        server_default=func.now(),  # → NOW() :: TIMESTAMPTZ
        default=datetime.now(timezone.utc),  # fallback client‑side
    )

    data_atualizacao = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.now(timezone.utc),
    )

    bairro          = relationship("Bairro", back_populates="validacoes")
    inspecoes       = relationship("Inspecao", back_populates="validacao",
                                   cascade="all, delete-orphan")


class Inspecao(Base):
    __tablename__ = "inspecoes"

    id   = Column(Integer, primary_key=True, index=True)

    validacao_id = Column(
        Integer,
        ForeignKey("validacoes.id", ondelete="CASCADE"),
        nullable=False,
    )

    ano   = Column(Integer, nullable=False)

    # Agora como ENUM
    edificacao_insercao = Column(
        PgEnum(StatusEdificacao, name="status_edificacao", create_type=False),
        nullable=False,
        default=StatusEdificacao.PENDENTE,
    )

    data_insercao = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    usuario = Column(String, nullable=False)

    validacao = relationship("Validacao", back_populates="inspecoes")