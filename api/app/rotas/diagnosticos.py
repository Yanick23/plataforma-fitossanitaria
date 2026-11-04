"""Sincronização de diagnósticos (RF09, RNF07), imagens e Grad-CAM."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .. import gradcam
from ..config import definicoes
from ..database import obter_sessao
from ..esquemas import DiagnosticoEnviar, DiagnosticoLer, ResultadoSincronizacao, SeguimentoEscrever
from ..regioes import filtro_zona, zona_de
from ..repositorios import diagnosticos as repo
from ..seguranca import UtilizadorActual
from ..servicos.diagnosticos import para_ler, pode_ver
from ..tabelas import Diagnostico, Distrito, Imagem, ModeloML, Patologia, Perfil, Seguimento, Utilizador, Validacao

router = APIRouter(tags=["Diagnósticos"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]

TIPOS_IMAGEM = {"image/jpeg": ".jpg", "image/png": ".png"}
TAMANHO_MAXIMO_IMAGEM = 10 * 1024 * 1024


@router.post("/diagnosticos", response_model=ResultadoSincronizacao)
async def enviar_diagnosticos(lote: list[DiagnosticoEnviar], utilizador: UtilizadorActual,
                              sessao: Sessao) -> ResultadoSincronizacao:
    """Recebe um lote de diagnósticos feitos offline.

    É idempotente: reenviar o mesmo UUID não cria duplicados, e o id volta como
    confirmado. A app só marca um diagnóstico como SINCRONIZADO depois de o ver
    em `confirmados`.
    """
    validas = {(p.cultura_id, p.codigo) for p in await sessao.scalars(select(Patologia))}
    ids = [str(d.id) for d in lote]
    existentes = {d.id: d for d in await sessao.scalars(select(Diagnostico).where(Diagnostico.id.in_(ids)))}

    confirmados, rejeitados = [], []
    vistos: set[str] = set()
    for d in lote:
        chave = str(d.id)
        if chave in vistos:  # o mesmo id repetido dentro do lote
            continue
        vistos.add(chave)
        existente = existentes.get(chave)
        if existente is not None:
            (confirmados if existente.utilizador_id == utilizador.id else rejeitados).append(d.id)
            continue
        if (d.cultura_id, d.classe_prevista) not in validas:
            rejeitados.append(d.id)
            continue
        sessao.add(Diagnostico(
            id=chave, utilizador_id=utilizador.id, cultura_id=d.cultura_id,
            classe_prevista=d.classe_prevista, confianca=d.confianca, data=d.data,
            versao_modelo=d.versao_modelo, tempo_inferencia_ms=d.tempo_inferencia_ms,
            distrito_id=utilizador.distrito_id,  # fica fixo, mesmo que o agricultor mude de distrito
        ))
        confirmados.append(d.id)
    await sessao.commit()
    return ResultadoSincronizacao(confirmados=confirmados, rejeitados=rejeitados)


async def _obter(sessao: AsyncSession, diagnostico_id: UUID) -> Diagnostico:
    d = await sessao.scalar(
        select(Diagnostico).where(Diagnostico.id == str(diagnostico_id))
        .options(selectinload(Diagnostico.imagem), selectinload(Diagnostico.utilizador),
                 selectinload(Diagnostico.distrito), selectinload(Diagnostico.seguimento),
                 selectinload(Diagnostico.validacao).selectinload(Validacao.tecnico)))
    if d is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diagnóstico não encontrado")
    return d


@router.post("/diagnosticos/{diagnostico_id}/imagem", status_code=status.HTTP_201_CREATED)
async def enviar_imagem(diagnostico_id: UUID, utilizador: UtilizadorActual, sessao: Sessao,
                        ficheiro: Annotated[UploadFile, File(description="Fotografia JPEG ou PNG")]) -> dict:
    d = await _obter(sessao, diagnostico_id)
    if d.utilizador_id != utilizador.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O diagnóstico pertence a outro utilizador")
    extensao = TIPOS_IMAGEM.get(ficheiro.content_type or "")
    if extensao is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "A imagem tem de ser JPEG ou PNG")
    conteudo = await ficheiro.read()
    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem maior que 10 MB")

    definicoes.pasta_imagens.mkdir(parents=True, exist_ok=True)
    destino = definicoes.pasta_imagens / f"{d.id}{extensao}"
    destino.write_bytes(conteudo)  # reenviar substitui o ficheiro: também é idempotente
    if d.imagem is None:
        sessao.add(Imagem(diagnostico_id=d.id, caminho_ficheiro=destino.name,
                          data_captura=d.data or datetime.now(timezone.utc)))
    else:
        d.imagem.caminho_ficheiro = destino.name
    await sessao.commit()
    return {"diagnostico_id": d.id, "bytes": len(conteudo)}


@router.get("/diagnosticos", response_model=list[DiagnosticoLer])
async def listar_diagnosticos(utilizador: UtilizadorActual, sessao: Sessao,
                              cultura: str | None = None) -> list[DiagnosticoLer]:
    """Agricultor: os seus (com a validação do técnico). Técnico: os da sua zona. Administrador: todos.

    O painel usa GET /gestao/diagnosticos, com filtros e paginação.
    """
    consulta = repo.consulta_base().order_by(Diagnostico.data.desc())
    if utilizador.perfil == Perfil.AGRICULTOR:
        consulta = consulta.where(Diagnostico.utilizador_id == utilizador.id)
    elif utilizador.perfil == Perfil.TECNICO:
        consulta = consulta.where(or_(
            filtro_zona(zona_de(utilizador), Diagnostico.distrito_id, Distrito.provincia_codigo, Utilizador.area),
            Diagnostico.utilizador_id == utilizador.id))
    if cultura:
        consulta = consulta.where(Diagnostico.cultura_id == cultura)
    return [para_ler(d) for d in await sessao.scalars(consulta)]


@router.get("/diagnosticos/{diagnostico_id}/imagem", response_class=FileResponse,
            responses={200: {"content": {"image/jpeg": {}, "image/png": {}}}})
async def obter_imagem(diagnostico_id: UUID, utilizador: UtilizadorActual, sessao: Sessao) -> FileResponse:
    """A fotografia original (para o painel e para a validação pelo técnico)."""
    d = await _obter(sessao, diagnostico_id)
    if not pode_ver(utilizador, d):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a este diagnóstico")
    caminho = Path(definicoes.pasta_imagens) / d.imagem.caminho_ficheiro if d.imagem else None
    if caminho is None or not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "A imagem deste diagnóstico não está no servidor")
    return FileResponse(caminho)


@router.get("/diagnosticos/{diagnostico_id}/gradcam", response_class=Response,
            responses={200: {"content": {"image/png": {}}, "description": "Mapa Grad-CAM sobreposto"}})
async def obter_gradcam(diagnostico_id: UUID, utilizador: UtilizadorActual, sessao: Sessao) -> Response:
    """Mapa de calor Grad-CAM da classe prevista, sobreposto à fotografia (secção 4.6.6)."""
    d = await _obter(sessao, diagnostico_id)
    if not pode_ver(utilizador, d):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a este diagnóstico")
    if d.imagem is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A imagem deste diagnóstico ainda não foi enviada")

    # A ordem das classes é a das saídas do modelo (lista guardada com o ModeloML).
    modelo = await sessao.scalar(select(ModeloML).where(ModeloML.cultura_id == d.cultura_id)
                                 .order_by(ModeloML.versao.desc()))
    classes = (json.loads(modelo.classes) if modelo else
               sorted(await sessao.scalars(select(Patologia.codigo).where(Patologia.cultura_id == d.cultura_id))))
    if d.classe_prevista not in classes:
        raise HTTPException(status.HTTP_409_CONFLICT, "Classe desconhecida para o modelo actual")

    caminho = Path(definicoes.pasta_imagens) / d.imagem.caminho_ficheiro
    try:
        png = await run_in_threadpool(gradcam.gerar_gradcam, d.cultura_id, caminho,
                                      classes.index(d.classe_prevista))
    except gradcam.ModeloIndisponivel as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from None
    return Response(content=png, media_type="image/png")


@router.post("/diagnosticos/{diagnostico_id}/seguimento", status_code=status.HTTP_204_NO_CONTENT)
async def responder_seguimento(diagnostico_id: UUID, dados: SeguimentoEscrever, utilizador: UtilizadorActual,
                               sessao: Sessao) -> None:
    """Dias depois do diagnóstico, o agricultor diz se seguiu a recomendação e se a planta melhorou."""
    d = await _obter(sessao, diagnostico_id)
    if d.utilizador_id != utilizador.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O diagnóstico pertence a outro utilizador")
    s = await sessao.get(Seguimento, d.id)
    if s is None:
        sessao.add(Seguimento(diagnostico_id=d.id, seguiu=dados.seguiu, resultado=dados.resultado,
                              comentario=(dados.comentario or "").strip() or None))
    else:  # responder outra vez substitui a resposta (também é idempotente)
        s.seguiu, s.resultado, s.comentario = dados.seguiu, dados.resultado, (dados.comentario or "").strip() or None
    await sessao.commit()
