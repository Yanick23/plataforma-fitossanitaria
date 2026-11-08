"""Validação pelo técnico, exactidão em campo e conjunto de retreino."""

import csv
import hashlib
import hmac
import io
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import definicoes
from ..esquemas import Confusao, ExactidaoCampo, ExactidaoClasse, ExactidaoDistrito, ExactidaoVersao, ValidacaoEscrever
from ..regioes import filtro_zona, zona_de
from ..repositorios import diagnosticos as repo
from ..tabelas import PERFIS_PESSOAL, Diagnostico, Distrito, Patologia, Utilizador, Validacao
from .auditoria import auditar
from .diagnosticos import pode_ver
from .notificacoes import avisar_declaracao
from .painel import descricao_zona


async def validar(sessao: AsyncSession, tecnico: Utilizador, d: Diagnostico, dados: ValidacaoEscrever) -> None:
    if tecnico.perfil not in PERFIS_PESSOAL or not pode_ver(tecnico, d):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Este diagnóstico não é da sua zona")
    patologia = await sessao.scalar(select(Patologia).where(
        Patologia.cultura_id == d.cultura_id, Patologia.codigo == dados.classe_confirmada))
    if patologia is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Classe inexistente para esta cultura")

    correcto = dados.classe_confirmada == d.classe_prevista
    nota = (dados.nota or "").strip() or None
    v = await sessao.get(Validacao, d.id)
    antes = None
    # 3b: avisar logo quando o caso passa a ser confirmado como praga de declaração obrigatória
    # (não se repete o aviso se a classe confirmada já era a mesma).
    novo_caso = patologia.declaracao_obrigatoria and (v is None or v.classe_confirmada != dados.classe_confirmada)
    if v is None:
        v = Validacao(diagnostico_id=d.id, tecnico_id=tecnico.id, classe_confirmada=dados.classe_confirmada,
                      correcto=correcto, nota=nota)
        sessao.add(v)
    else:
        antes = {"classe_confirmada": v.classe_confirmada, "nota": v.nota, "tecnico_id": v.tecnico_id}
        v.tecnico_id, v.classe_confirmada, v.correcto, v.nota = tecnico.id, dados.classe_confirmada, correcto, nota
    auditar(sessao, tecnico, "diagnostico.validar", "diagnostico", d.id, antes=antes, depois={
        "classe_prevista": d.classe_prevista, "classe_confirmada": dados.classe_confirmada, "nota": nota})
    if novo_caso:
        await avisar_declaracao(sessao, tecnico, d, patologia)
    await sessao.commit()


async def exactidao(sessao: AsyncSession, utilizador: Utilizador, cultura: str | None = None,
                    desde: datetime | None = None) -> ExactidaoCampo:
    zona = zona_de(utilizador)

    def da_zona(*colunas):
        q = (select(*colunas).select_from(Diagnostico)
             .join(Utilizador, Utilizador.id == Diagnostico.utilizador_id)
             .outerjoin(Distrito, Distrito.id == Diagnostico.distrito_id)
             .where(filtro_zona(zona, Diagnostico.distrito_id, Distrito.provincia_codigo, Utilizador.area)))
        if cultura:
            q = q.where(Diagnostico.cultura_id == cultura)
        if desde:
            q = q.where(Diagnostico.data >= desde)
        return q

    validados = list(await sessao.execute(
        da_zona(Diagnostico.cultura_id, Diagnostico.classe_prevista, Diagnostico.versao_modelo,
                Validacao.classe_confirmada, Validacao.correcto, Diagnostico.distrito_id, Distrito.nome)
        .join(Validacao, Validacao.diagnostico_id == Diagnostico.id)))
    pendentes = await sessao.scalar(
        da_zona(func.count(Diagnostico.id)).outerjoin(Validacao, Validacao.diagnostico_id == Diagnostico.id)
        .where(Validacao.diagnostico_id.is_(None))) or 0
    nomes = {(p.cultura_id, p.codigo): p.nome_local for p in await sessao.scalars(select(Patologia))}

    por_classe, por_versao, confusoes = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(int)
    por_distrito = defaultdict(lambda: [0, 0])
    for c, prevista, versao, confirmada, correcto, distrito_id, distrito_nome in validados:
        por_distrito[(distrito_id, distrito_nome or "Sem distrito")][0] += 1
        por_distrito[(distrito_id, distrito_nome or "Sem distrito")][1] += int(correcto)
        por_classe[(c, confirmada)][0] += 1          # a classe real é a confirmada pelo técnico
        por_classe[(c, confirmada)][1] += int(correcto)
        por_versao[(c, versao)][0] += 1
        por_versao[(c, versao)][1] += int(correcto)
        if not correcto:
            confusoes[(c, prevista, confirmada)] += 1

    def taxa(n, k):
        return round(k / n, 4) if n else None

    total_ok = sum(int(r[4]) for r in validados)
    return ExactidaoCampo(
        zona=await descricao_zona(sessao, utilizador), validados=len(validados), correctos=total_ok,
        exactidao=taxa(len(validados), total_ok), pendentes=pendentes,
        por_classe=sorted((ExactidaoClasse(classe=f"{c}:{k}", nome=nomes.get((c, k), k), validados=n,
                                           correctos=ok, exactidao=taxa(n, ok))
                           for (c, k), (n, ok) in por_classe.items()), key=lambda x: (-x.validados, x.nome)),
        por_versao=sorted((ExactidaoVersao(cultura_id=c, versao_modelo=v, validados=n, correctos=ok,
                                           exactidao=taxa(n, ok))
                           for (c, v), (n, ok) in por_versao.items()),
                          key=lambda x: (x.cultura_id, x.versao_modelo or 0)),
        por_distrito=sorted((ExactidaoDistrito(distrito_id=d, distrito=n, validados=v, correctos=ok,
                                               exactidao=taxa(v, ok))
                             for (d, n), (v, ok) in por_distrito.items()), key=lambda x: (-x.validados, x.distrito)),
        confusoes=sorted((Confusao(cultura_id=c, prevista=p, confirmada=k, total=n)
                          for (c, p, k), n in confusoes.items()), key=lambda x: -x.total),
    )


# Divisão para retreino, como a do CCMT: 70% treino, 15% validação, 15% teste, fixa entre exportações.
DIVISAO = (("treino", 70), ("validacao", 15), ("teste", 15))
LEIA_ME = """Conjunto de retreino exportado da plataforma (fotografias validadas pelos técnicos).

rotulos.csv: uma linha por diagnóstico validado. A classe verdadeira é classe_confirmada.

Divisão (coluna subconjunto): 70% treino, 15% validação, 15% teste. As fotografias do mesmo
agricultor no mesmo dia (coluna grupo) ficam sempre no mesmo subconjunto, como as fotografias da
mesma folha na divisão do CCMT, para não haver fuga de dados entre treino e teste. A divisão é
fixa: o mesmo grupo cai sempre no mesmo subconjunto, de uma exportação para a seguinte.
"""


def grupo_de(d: Diagnostico) -> str:
    """Fotografias que provavelmente mostram as mesmas plantas: mesmo agricultor, mesmo dia.
    Código não reversível (HMAC com a chave do servidor): o investigador também exporta este ficheiro."""
    data = d.data if d.data.tzinfo else d.data.replace(tzinfo=timezone.utc)
    chave = f"{d.utilizador_id}-{data.date().isoformat()}".encode()
    return hmac.new(definicoes.jwt_segredo.encode(), chave, hashlib.sha256).hexdigest()[:12]


def subconjunto_de(grupo: str) -> str:
    """Divisão determinística por grupo (resumo SHA-256 em 100 partes)."""
    n = int(hashlib.sha256(grupo.encode()).hexdigest(), 16) % 100
    limite = 0
    for nome, pct in DIVISAO:
        limite += pct
        if n < limite:
            return nome
    return DIVISAO[-1][0]


async def exportar_validados(sessao: AsyncSession) -> bytes:
    """ZIP com as fotografias validadas (pasta por cultura/classe confirmada), um CSV com os rótulos
    e a divisão treino/validação/teste por grupo, e um LEIA-ME."""
    linhas = list(await sessao.scalars(
        repo.consulta_base().where(Validacao.diagnostico_id.is_not(None)).order_by(Diagnostico.data)))
    memoria = io.BytesIO()
    tabela = io.StringIO()
    escritor = csv.writer(tabela)
    escritor.writerow(["ficheiro", "diagnostico_id", "cultura", "classe_confirmada", "classe_prevista",
                       "confianca", "correcto", "distrito", "provincia", "data", "versao_modelo", "tecnico",
                       "grupo", "subconjunto"])
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        for d in linhas:
            v = d.validacao
            origem = Path(definicoes.pasta_imagens) / d.imagem.caminho_ficheiro if d.imagem else None
            nome = ""
            if origem is not None and origem.exists():
                nome = f"{d.cultura_id}/{v.classe_confirmada}/{d.id}{origem.suffix}"
                z.write(origem, nome)
            escritor.writerow([nome, d.id, d.cultura_id, v.classe_confirmada, d.classe_prevista,
                               round(d.confianca, 4), int(v.correcto), d.distrito.nome if d.distrito else "",
                               d.distrito.provincia_codigo if d.distrito else "", d.data.isoformat(),
                               d.versao_modelo or "", v.tecnico.nome if v.tecnico else "",
                               grupo_de(d), subconjunto_de(grupo_de(d))])
        z.writestr("rotulos.csv", tabela.getvalue())
        z.writestr("LEIA-ME.txt", LEIA_ME)
    return memoria.getvalue()

