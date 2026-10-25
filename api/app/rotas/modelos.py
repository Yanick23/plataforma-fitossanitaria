"""Versões do modelo TFLite por cultura (RF12)."""

import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import definicoes
from ..database import obter_sessao
from ..esquemas import ModeloLer
from ..seguranca import Administrador, Pessoal, UtilizadorActual
from ..servicos.auditoria import auditar
from ..tabelas import Cultura, ModeloML

router = APIRouter(tags=["Modelos"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


def _para_ler(m: ModeloML, pedido: Request) -> ModeloLer:
    return ModeloLer(
        cultura_id=m.cultura_id, versao=m.versao, classes=json.loads(m.classes),
        acuracia_teste=m.acuracia_teste, tamanho_bytes=m.tamanho_bytes, sha256=m.sha256,
        url_ficheiro=str(pedido.url_for("descarregar_modelo", cultura=m.cultura_id, versao=m.versao)),
        criado_em=m.criado_em,
    )


@router.get("/modelos/{cultura}", response_model=list[ModeloLer])
async def historico(cultura: str, pedido: Request, _: Pessoal, sessao: Sessao) -> list[ModeloLer]:
    """Todas as versões publicadas de uma cultura (a mais recente primeiro)."""
    modelos = await sessao.scalars(select(ModeloML).where(ModeloML.cultura_id == cultura)
                                   .order_by(ModeloML.versao.desc()))
    return [_para_ler(m, pedido) for m in modelos]


@router.get("/modelos/{cultura}/ultima-versao", response_model=ModeloLer)
async def ultima_versao(cultura: str, pedido: Request, _: UtilizadorActual, sessao: Sessao) -> ModeloLer:
    modelo = await sessao.scalar(select(ModeloML).where(ModeloML.cultura_id == cultura)
                                 .order_by(ModeloML.versao.desc()))
    if modelo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ainda não há modelos para esta cultura")
    return _para_ler(modelo, pedido)


@router.get("/modelos/{cultura}/{versao}/ficheiro", name="descarregar_modelo", response_class=FileResponse)
async def descarregar(cultura: str, versao: int, _: UtilizadorActual, sessao: Sessao) -> FileResponse:
    modelo = await sessao.scalar(select(ModeloML).where(
        (ModeloML.cultura_id == cultura) & (ModeloML.versao == versao)))
    caminho = definicoes.pasta_modelos / modelo.caminho_tflite if modelo else None
    if caminho is None or not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Modelo não encontrado")
    return FileResponse(caminho, media_type="application/octet-stream", filename=caminho.name)


@router.post("/modelos/{cultura}", response_model=ModeloLer, status_code=status.HTTP_201_CREATED)
async def publicar_modelo(
    cultura: str, pedido: Request, admin: Administrador, sessao: Sessao,
    ficheiro: Annotated[UploadFile, File(description="Modelo .tflite (entrada float32 [1,224,224,3])")],
    classes: Annotated[str, Form(description='Lista JSON pela ordem das saídas, ex.: ["acaro_verde", ...]')],
    acuracia_teste: Annotated[float | None, Form(ge=0, le=1)] = None,
) -> ModeloLer:
    """O administrador publica uma nova versão; as apps descarregam-na na próxima sincronização."""
    if await sessao.get(Cultura, cultura) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura inexistente")
    try:
        lista = json.loads(classes)
        assert isinstance(lista, list) and lista and all(isinstance(c, str) for c in lista)
    except (ValueError, AssertionError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "classes tem de ser uma lista JSON de textos") from None

    conteudo = await ficheiro.read()
    if not conteudo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ficheiro vazio")
    versao = (await sessao.scalar(select(func.max(ModeloML.versao)).where(ModeloML.cultura_id == cultura)) or 0) + 1
    nome = f"modelo_{cultura}_v{versao}.tflite"
    definicoes.pasta_modelos.mkdir(parents=True, exist_ok=True)
    (definicoes.pasta_modelos / nome).write_bytes(conteudo)

    modelo = ModeloML(cultura_id=cultura, versao=versao, caminho_tflite=nome, classes=json.dumps(lista),
                      acuracia_teste=acuracia_teste, tamanho_bytes=len(conteudo),
                      sha256=hashlib.sha256(conteudo).hexdigest())
    sessao.add(modelo)
    auditar(sessao, admin, "modelo.publicar", "modelo", f"{cultura} v{versao}",
            depois={"sha256": modelo.sha256, "tamanho_bytes": modelo.tamanho_bytes, "classes": lista,
                    "acuracia_teste": acuracia_teste})
    await sessao.commit()
    return _para_ler(modelo, pedido)
