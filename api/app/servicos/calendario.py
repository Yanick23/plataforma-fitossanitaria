"""Calendário agrícola por província (funcionalidade 10).

Os dados estão em app/calendario_agricola.json, com a fonte de cada linha: actividades do ano
típico por região (FEWS NET), época habitual de sementeira por província (MASA) e avisos de
vigilância por mês, só com confiança alta ou média. A app guarda o calendário da província do
agricultor na sincronização e mostra «Nesta altura…» sem Internet.
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import AvisoCalendario, Calendario, FonteCalendario, MesCalendario
from ..tabelas import Patologia, Provincia

FICHEIRO = Path(__file__).resolve().parent.parent / "calendario_agricola.json"


@lru_cache
def dados() -> dict:
    return json.loads(FICHEIRO.read_text(encoding="utf-8"))


def regiao_de(provincia_codigo: str) -> str | None:
    for codigo, r in dados()["regioes"].items():
        if provincia_codigo in r["provincias"]:
            return codigo
    return None


async def calendario(sessao: AsyncSession, provincia_codigo: str) -> Calendario:
    provincia = await sessao.get(Provincia, provincia_codigo)
    regiao = regiao_de(provincia_codigo)
    if provincia is None or regiao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Província sem calendário")
    d = dados()
    nomes = {(p.cultura_id, p.codigo): p.nome_local for p in await sessao.scalars(select(Patologia))}

    meses = []
    usadas = set(d["fonte_actividades"]) | set(d["fonte_sementeira"])
    for mes in range(1, 13):
        avisos = []
        for a in d["avisos"]:
            if mes in a["meses"].get(regiao, []):
                avisos.append(AvisoCalendario(
                    cultura_id=a["cultura_id"], classe=a["classe"],
                    patologia_nome=nomes.get((a["cultura_id"], a["classe"])) if a["classe"] else None,
                    texto=a["texto"], confianca=a["confianca"], fontes=a["fontes"]))
                usadas.update(a["fontes"])
        meses.append(MesCalendario(mes=mes, actividades=d["actividades"][regiao][str(mes)], avisos=avisos))

    return Calendario(
        provincia_codigo=provincia_codigo, provincia=provincia.nome, regiao=d["regioes"][regiao]["nome"],
        sementeira=d["sementeira"].get(provincia_codigo), meses=meses, aviso=d["aviso"],
        fontes=[FonteCalendario(id=f, referencia=d["fontes"][f]["referencia"], url=d["fontes"][f].get("url"))
                for f in d["fontes"] if f in usadas])
