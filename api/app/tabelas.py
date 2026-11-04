"""Tabelas da base de dados (diagrama de classes, secção 5.3.3).

Utilizador, Cultura, Patologia, Diagnostico, Imagem e ModeloML; Provincia e Distrito
(divisão administrativa de Moçambique); Alerta e AlertaLeitura (avisos por zona).
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, false,
                        true)
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


class NivelAlerta(str, enum.Enum):
    INFORMACAO = "INFORMACAO"
    AVISO = "AVISO"
    URGENTE = "URGENTE"


class Provincia(Base):
    __tablename__ = "provincias"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)  # ISO 3166-2, ex.: "MZ-L"
    nome: Mapped[str] = mapped_column(String(60))

    distritos: Mapped[list["Distrito"]] = relationship(back_populates="provincia")


class Distrito(Base):
    __tablename__ = "distritos"
    __table_args__ = (UniqueConstraint("provincia_codigo", "nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    provincia_codigo: Mapped[str] = mapped_column(ForeignKey("provincias.codigo"), index=True)

    provincia: Mapped[Provincia] = relationship(back_populates="distritos")


class Utilizador(Base):
    __tablename__ = "utilizadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    hash_palavra_passe: Mapped[str] = mapped_column(String(100))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, name="perfil"), default=Perfil.AGRICULTOR)
    # Área em texto livre (como foi escrita no registo); a zona oficial é o distrito/província.
    area: Mapped[str | None] = mapped_column(String(80), index=True)
    # Zona: o agricultor pertence a um distrito; o técnico actua num distrito ou, sem distrito,
    # numa província inteira; o administrador actua no país todo.
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"), index=True)
    provincia_codigo: Mapped[str | None] = mapped_column(ForeignKey("provincias.codigo"), index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="utilizador")
    distrito: Mapped[Distrito | None] = relationship()


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
    # Fase 2: catálogo enriquecido e controlo do conteúdo.
    sintomas: Mapped[str | None] = mapped_column(Text)
    prevencao: Mapped[str | None] = mapped_column(Text)
    declaracao_obrigatoria: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    versao_conteudo: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    validado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"))
    validado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cultura: Mapped[Cultura] = relationship(back_populates="patologias")
    validado_por: Mapped["Utilizador | None"] = relationship()
    fotos: Mapped[list["FotoReferencia"]] = relationship(back_populates="patologia", cascade="all, delete-orphan",
                                                         passive_deletes=True, order_by="FotoReferencia.id")


class FotoReferencia(Base):
    """Fotografia de referência de uma praga/doença (ajuda o agricultor a comparar)."""

    __tablename__ = "fotos_referencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    patologia_id: Mapped[int] = mapped_column(ForeignKey("patologias.id", ondelete="CASCADE"), index=True)
    caminho_ficheiro: Mapped[str] = mapped_column(String(300))
    legenda: Mapped[str | None] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    patologia: Mapped[Patologia] = relationship(back_populates="fotos")


class EstadoModelo(str, enum.Enum):
    PILOTO = "PILOTO"        # só os agricultores dos distritos piloto o recebem
    PUBLICADO = "PUBLICADO"  # todos o recebem
    RETIRADO = "RETIRADO"    # ninguém o recebe (volta-se à versão publicada anterior)


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
    estado: Mapped[EstadoModelo] = mapped_column(Enum(EstadoModelo, name="estado_modelo"),
                                                 default=EstadoModelo.PUBLICADO, server_default="PUBLICADO")
    distritos_piloto: Mapped[str | None] = mapped_column(Text)  # JSON: lista de ids de distritos
    notas: Mapped[str | None] = mapped_column(Text)


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
    # Distrito do agricultor no momento em que o diagnóstico chegou (fica fixo no histórico).
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"), index=True)

    utilizador: Mapped[Utilizador] = relationship(back_populates="diagnosticos")
    imagem: Mapped["Imagem | None"] = relationship(back_populates="diagnostico", uselist=False)
    distrito: Mapped[Distrito | None] = relationship()
    validacao: Mapped["Validacao | None"] = relationship(uselist=False, viewonly=True)
    seguimento: Mapped["Seguimento | None"] = relationship(uselist=False, viewonly=True)


class Imagem(Base):
    __tablename__ = "imagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostico_id: Mapped[str] = mapped_column(ForeignKey("diagnosticos.id"), unique=True)
    caminho_ficheiro: Mapped[str] = mapped_column(String(300))
    data_captura: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    diagnostico: Mapped[Diagnostico] = relationship(back_populates="imagem")


class Alerta(Base):
    """Aviso enviado aos agricultores de uma zona (distrito, província ou país todo)."""

    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    mensagem: Mapped[str] = mapped_column(Text)
    nivel: Mapped[NivelAlerta] = mapped_column(Enum(NivelAlerta, name="nivel_alerta"), default=NivelAlerta.AVISO)
    cultura_id: Mapped[str | None] = mapped_column(ForeignKey("culturas.id"))
    patologia_id: Mapped[int | None] = mapped_column(ForeignKey("patologias.id", ondelete="SET NULL"))
    # Zona: distrito > província > (nenhum dos dois) país todo.
    provincia_codigo: Mapped[str | None] = mapped_column(ForeignKey("provincias.codigo"), index=True)
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"), index=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arquivado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    autor: Mapped[Utilizador] = relationship()
    patologia: Mapped[Patologia | None] = relationship()
    distrito: Mapped[Distrito | None] = relationship()
    provincia: Mapped[Provincia | None] = relationship()


class AlertaLeitura(Base):
    """Regista que um agricultor recebeu e abriu um alerta (para medir o alcance)."""

    __tablename__ = "alertas_leituras"

    alerta_id: Mapped[int] = mapped_column(ForeignKey("alertas.id", ondelete="CASCADE"), primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"), primary_key=True)
    lido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class EstadoVisita(str, enum.Enum):
    PENDENTE = "PENDENTE"
    AGENDADA = "AGENDADA"
    RESOLVIDA = "RESOLVIDA"
    CANCELADA = "CANCELADA"


class Validacao(Base):
    """O técnico confirma ou corrige a classe prevista pelo modelo (exactidão em campo)."""

    __tablename__ = "validacoes"

    diagnostico_id: Mapped[str] = mapped_column(ForeignKey("diagnosticos.id", ondelete="CASCADE"), primary_key=True)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"))
    classe_confirmada: Mapped[str] = mapped_column(String(60))
    correcto: Mapped[bool] = mapped_column(Boolean)  # classe_confirmada == classe prevista pelo modelo
    nota: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    actualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    tecnico: Mapped[Utilizador] = relationship()


class PedidoVisita(Base):
    """O agricultor pede ajuda a partir de um diagnóstico; o técnico agenda e resolve."""

    __tablename__ = "pedidos_visita"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostico_id: Mapped[str] = mapped_column(ForeignKey("diagnosticos.id", ondelete="CASCADE"), index=True)
    agricultor_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"), index=True)
    tecnico_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"))
    distrito_id: Mapped[int | None] = mapped_column(ForeignKey("distritos.id"), index=True)
    estado: Mapped[EstadoVisita] = mapped_column(Enum(EstadoVisita, name="estado_visita"), default=EstadoVisita.PENDENTE)
    mensagem: Mapped[str | None] = mapped_column(Text)
    data_agendada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notas_tecnico: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    actualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    diagnostico: Mapped[Diagnostico] = relationship()
    agricultor: Mapped[Utilizador] = relationship(foreign_keys=[agricultor_id])
    tecnico: Mapped[Utilizador | None] = relationship(foreign_keys=[tecnico_id])
    distrito: Mapped[Distrito | None] = relationship()


class RegistoAuditoria(Base):
    """Quem fez o quê e quando (alterações ao catálogo, alertas, contas, validações...)."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilizador_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), index=True)
    accao: Mapped[str] = mapped_column(String(60), index=True)  # ex.: "patologia.actualizar"
    entidade: Mapped[str] = mapped_column(String(40))
    entidade_id: Mapped[str | None] = mapped_column(String(60))
    detalhes: Mapped[str | None] = mapped_column(Text)  # JSON: {"antes": ..., "depois": ...}
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)

    utilizador: Mapped[Utilizador | None] = relationship()


class Seguiu(str, enum.Enum):
    SIM = "SIM"
    PARCIAL = "PARCIAL"
    NAO = "NAO"


class ResultadoTratamento(str, enum.Enum):
    MELHOROU = "MELHOROU"
    IGUAL = "IGUAL"
    PIOROU = "PIOROU"
    NAO_SEI = "NAO_SEI"


class Seguimento(Base):
    """Resposta do agricultor, dias depois: seguiu a recomendação? A planta melhorou?"""

    __tablename__ = "seguimentos"

    diagnostico_id: Mapped[str] = mapped_column(ForeignKey("diagnosticos.id", ondelete="CASCADE"), primary_key=True)
    seguiu: Mapped[Seguiu] = mapped_column(Enum(Seguiu, name="seguiu"))
    resultado: Mapped[ResultadoTratamento] = mapped_column(Enum(ResultadoTratamento, name="resultado_tratamento"))
    comentario: Mapped[str | None] = mapped_column(Text)
    respondido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
