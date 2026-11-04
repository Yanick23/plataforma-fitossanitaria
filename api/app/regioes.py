"""Divisão administrativa de Moçambique e zona de actuação de cada utilizador."""

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import ColumnElement, and_, false, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from .tabelas import Distrito, Perfil, Provincia, Utilizador

FICHEIRO = Path(__file__).with_name("regioes_mocambique.json")


def normalizar(texto: str) -> str:
    """'Chókwè' -> 'chokwe'; 'Cidade de Maputo' -> 'cidade de maputo'."""
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acentos.lower().replace("-", " ").split())


def carregar_regioes() -> dict:
    return json.loads(FICHEIRO.read_text(encoding="utf-8"))


async def distrito_por_nome(sessao: AsyncSession, nome: str | None) -> Distrito | None:
    """Encontra o distrito escrito em texto livre no registo (ex.: 'Boane', 'matola', 'Chokwè')."""
    if not nome or not nome.strip():
        return None
    alvo = normalizar(nome)
    distritos = list(await sessao.scalars(select(Distrito)))
    for d in distritos:
        n = normalizar(d.nome)
        if alvo in (n, n.removeprefix("cidade de "), n.removeprefix("cidade da ")):
            return d
    return None


async def resolver_zona(sessao: AsyncSession, distrito_id: int | None, area: str | None,
                        provincia_codigo: str | None = None) -> tuple[Distrito | None, str | None]:
    """Distrito e província de uma conta: o distrito escolhido na lista, senão o da área escrita."""
    from fastapi import HTTPException, status

    if distrito_id is not None:
        distrito = await sessao.get(Distrito, distrito_id)
        if distrito is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Distrito inexistente")
    else:
        distrito = await distrito_por_nome(sessao, area)
    if distrito is not None:
        return distrito, distrito.provincia_codigo
    if provincia_codigo is not None and await sessao.get(Provincia, provincia_codigo) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Província inexistente")
    return None, provincia_codigo


@dataclass(frozen=True)
class Zona:
    """Onde um utilizador actua. nacional=True para o administrador."""

    nacional: bool = False
    provincia_codigo: str | None = None
    distrito_id: int | None = None
    area_texto: str | None = None  # só para contas antigas sem distrito reconhecido

    @property
    def vazia(self) -> bool:
        return not (self.nacional or self.provincia_codigo or self.distrito_id or self.area_texto)

    def descricao(self) -> str:
        if self.nacional:
            return "Todo o país"
        if self.distrito_id:
            return f"distrito {self.distrito_id}"
        return self.provincia_codigo or self.area_texto or "sem zona"


def zona_de(u: Utilizador) -> Zona:
    if u.perfil == Perfil.ADMINISTRADOR:
        return Zona(nacional=True)
    if u.distrito_id:
        return Zona(distrito_id=u.distrito_id)
    if u.provincia_codigo:
        return Zona(provincia_codigo=u.provincia_codigo)
    return Zona(area_texto=u.area)


def filtro_zona(zona: Zona, coluna_distrito, coluna_provincia, coluna_area=None) -> ColumnElement[bool]:
    """Condição SQL 'está dentro desta zona' para tabelas com distrito/província (e área antiga)."""
    if zona.nacional:
        return true()
    if zona.distrito_id:
        return coluna_distrito == zona.distrito_id
    if zona.provincia_codigo:
        return coluna_provincia == zona.provincia_codigo
    if zona.area_texto and coluna_area is not None:
        return and_(coluna_area.is_not(None), coluna_area == zona.area_texto)
    return false()


def zona_contem(exterior: Zona, provincia_codigo: str | None, distrito_id: int | None,
                provincia_do_distrito: str | None) -> bool:
    """A zona `exterior` (de quem envia) cobre o destino (província/distrito escolhido)?"""
    if exterior.nacional:
        return True
    if exterior.distrito_id:
        return distrito_id == exterior.distrito_id
    if exterior.provincia_codigo:
        destino = provincia_do_distrito if distrito_id else provincia_codigo
        return destino == exterior.provincia_codigo
    return False


def condicao_utilizador_na_zona(zona: Zona) -> ColumnElement[bool]:
    """Utilizadores (agricultores) que pertencem à zona, pelo distrito ou pela área antiga."""
    if zona.nacional:
        return true()
    if zona.distrito_id:
        return Utilizador.distrito_id == zona.distrito_id
    if zona.provincia_codigo:
        return Utilizador.distrito_id.in_(
            select(Distrito.id).where(Distrito.provincia_codigo == zona.provincia_codigo))
    if zona.area_texto:
        return or_(Utilizador.area == zona.area_texto)
    return false()
