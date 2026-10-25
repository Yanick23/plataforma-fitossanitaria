"""Dados iniciais: 2 culturas, 12 patologias, administrador e modelos v1.

Corre no arranque da API e só insere o que ainda não existe.
"""

import hashlib
import json
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import definicoes
from .regioes import carregar_regioes, distrito_por_nome
from .seguranca import gerar_hash
from .tabelas import (Cultura, Diagnostico, Distrito, ModeloML, Patologia, Perfil, Provincia, TipoPatologia,
                      Utilizador)

CATALOGO = Path(__file__).with_name("catalogo_inicial.json")

CULTURAS = {
    "milho": ("Milho", "Zea mays"),
    "mandioca": ("Mandioca", "Manihot esculenta"),
}


def resumo_ficheiro(caminho: Path) -> tuple[int, str]:
    dados = caminho.read_bytes()
    return len(dados), hashlib.sha256(dados).hexdigest()


async def semear(sessao: AsyncSession) -> None:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))

    for cultura_id, (nome, cientifico) in CULTURAS.items():
        if await sessao.get(Cultura, cultura_id) is None:
            sessao.add(Cultura(id=cultura_id, nome=nome, nome_cientifico=cientifico))
    await sessao.flush()

    for cultura_id in CULTURAS:
        existentes = set(await sessao.scalars(
            select(Patologia.codigo).where(Patologia.cultura_id == cultura_id)))
        for codigo, p in catalogo[cultura_id].items():
            if codigo not in existentes:
                sessao.add(Patologia(
                    cultura_id=cultura_id, codigo=codigo, nome_local=p["nome_local"],
                    nome_cientifico=p["nome_cientifico"], tipo=TipoPatologia(p["tipo"].upper()),
                    recomendacao=p["recomendacao"],
                ))

        # Versão 1 do modelo = a que vem dentro da app, se o ficheiro estiver em api/modelos/.
        tflite = definicoes.pasta_modelos / f"modelo_{cultura_id}_int8_dinamica.tflite"
        classes = definicoes.pasta_modelos / f"classes_{cultura_id}.json"
        ja_tem = await sessao.scalar(select(ModeloML).where(ModeloML.cultura_id == cultura_id))
        if ja_tem is None and tflite.exists():
            tamanho, sha = resumo_ficheiro(tflite)
            lista_classes = (json.loads(classes.read_text(encoding="utf-8")) if classes.exists()
                             else sorted(catalogo[cultura_id]))
            sessao.add(ModeloML(
                cultura_id=cultura_id, versao=1, caminho_tflite=tflite.name,
                classes=json.dumps(lista_classes), tamanho_bytes=tamanho, sha256=sha,
            ))

    if definicoes.admin_telefone and definicoes.admin_palavra_passe:
        existe = await sessao.scalar(
            select(Utilizador).where(Utilizador.telefone == definicoes.admin_telefone))
        if existe is None:
            sessao.add(Utilizador(
                nome=definicoes.admin_nome, telefone=definicoes.admin_telefone,
                hash_palavra_passe=gerar_hash(definicoes.admin_palavra_passe),
                perfil=Perfil.ADMINISTRADOR,
            ))

    await semear_regioes(sessao)
    await sessao.commit()


async def semear_regioes(sessao: AsyncSession) -> None:
    """11 províncias e 157 distritos; liga as contas antigas ao distrito escrito na área."""
    regioes = carregar_regioes()
    for p in regioes["provincias"]:
        if await sessao.get(Provincia, p["codigo"]) is None:
            sessao.add(Provincia(codigo=p["codigo"], nome=p["nome"]))
    await sessao.flush()
    existentes = {(d.provincia_codigo, d.nome) for d in await sessao.scalars(select(Distrito))}
    for d in regioes["distritos"]:
        if (d["provincia"], d["nome"]) not in existentes:
            sessao.add(Distrito(nome=d["nome"], provincia_codigo=d["provincia"]))
    await sessao.flush()

    sem_distrito = await sessao.scalars(select(Utilizador).where(
        Utilizador.distrito_id.is_(None), Utilizador.area.is_not(None),
        Utilizador.perfil != Perfil.ADMINISTRADOR))
    for u in sem_distrito:
        if (d := await distrito_por_nome(sessao, u.area)) is not None:
            u.distrito_id, u.provincia_codigo = d.id, d.provincia_codigo
    await sessao.flush()
    # Diagnósticos antigos ficam com o distrito do agricultor.
    await sessao.execute(update(Diagnostico).where(Diagnostico.distrito_id.is_(None)).values(
        distrito_id=select(Utilizador.distrito_id).where(Utilizador.id == Diagnostico.utilizador_id)
        .scalar_subquery()))
