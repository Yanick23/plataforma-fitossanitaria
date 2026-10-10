"""Tabelas da base de dados (diagrama de classes, secção 5.3.3).

Utilizador, Cultura, Patologia, Diagnostico, Imagem e ModeloML.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Perfil(str, enum.Enum):
    AGRICULTOR = "AGRICULTOR"
    TECNICO = "TECNICO"
    ADMINISTRADOR = "ADMINISTRADOR"


class TipoPatologia(str, enum.Enum):
    DOENCA = "DOENCA"
    PRAGA = "PRAGA"
    SAUDAVEL = "SAUDAVEL"


class Utilizador(Base):
    __tablename__ = "utilizadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    hash_palavra_passe: Mapped[str] = mapped_column(String(100))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, name="perfil"), default=Perfil.AGRICULTOR)
    # Área de actuação (ex.: distrito). O técnico vê os diagnósticos dos agricultores da sua área.
    area: Mapped[str | None] = mapped_column(String(80), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="utilizador")


class Cultura(Base):
    __tablename__ = "culturas"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)  # "milho", "mandioca"
    nome: Mapped[str] = mapped_column(String(60))
    nome_cientifico: Mapped[str] = mapped_column(String(120))

    patologias: Mapped[list["Patologia"]] = relationship(back_populates="cultura")


class Patologia(Base):
    """Uma classe do modelo: doença, praga ou folha saudável."""

    __tablename__ = "patologias"
    __table_args__ = (UniqueConstraint("cultura_id", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cultura_id: Mapped[str] = mapped_column(ForeignKey("culturas.id"))
    codigo: Mapped[str] = mapped_column(String(60))  # igual à classe do modelo, ex.: "mosaico"
    nome_local: Mapped[str] = mapped_column(String(120))
    nome_cientifico: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[TipoPatologia] = mapped_column(Enum(TipoPatologia, name="tipo_patologia"))
    recomendacao: Mapped[str] = mapped_column(Text)

    cultura: Mapped[Cultura] = relationship(back_populates="patologias")


class ModeloML(Base):
    __tablename__ = "modelos_ml"
    __table_args__ = (UniqueConstraint("cultura_id", "versao"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cultura_id: Mapped[str] = mapped_column(ForeignKey("culturas.id"))
    versao: Mapped[int] = mapped_column(Integer)
    caminho_tflite: Mapped[str] = mapped_column(String(300))
    classes: Mapped[str] = mapped_column(Text)  # JSON: lista pela ordem das saídas do modelo
    acuracia_teste: Mapped[float | None] = mapped_column(Float)
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    # UUID gerado no telemóvel: garante que um reenvio não cria duplicados (RNF07).
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"), index=True)
    cultura_id: Mapped[str] = mapped_column(ForeignKey("culturas.id"))
    classe_prevista: Mapped[str] = mapped_column(String(60))
    confianca: Mapped[float] = mapped_column(Float)
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    versao_modelo: Mapped[int | None] = mapped_column(Integer)
    tempo_inferencia_ms: Mapped[int | None] = mapped_column(Integer)
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    utilizador: Mapped[Utilizador] = relationship(back_populates="diagnosticos")
    imagem: Mapped["Imagem | None"] = relationship(back_populates="diagnostico", uselist=False)


class Imagem(Base):
    __tablename__ = "imagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostico_id: Mapped[str] = mapped_column(ForeignKey("diagnosticos.id"), unique=True)
    caminho_ficheiro: Mapped[str] = mapped_column(String(300))
    data_captura: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    diagnostico: Mapped[Diagnostico] = relationship(back_populates="imagem")
