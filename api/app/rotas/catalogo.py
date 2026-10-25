"""Culturas e patologias (RF11). Leitura para todos; escrita só para o administrador (com auditoria)."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import definicoes
from ..database import obter_sessao
from ..esquemas import (CulturaCriar, CulturaEscrever, CulturaLer, FotoLer, PatologiaCriar, PatologiaEscrever,
                        PatologiaLer)
from ..seguranca import Administrador, Pessoal
from ..servicos.auditoria import auditar, instantaneo
from ..tabelas import Cultura, FotoReferencia, Patologia

router = APIRouter(tags=["Catálogo"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]

CAMPOS_TEXTO = ("nome_local", "nome_cientifico", "recomendacao", "sintomas", "prevencao")
CAMPOS_PATOLOGIA = ("cultura_id", "codigo", "tipo", "declaracao_obrigatoria", *CAMPOS_TEXTO)


@router.get("/culturas", response_model=list[CulturaLer])
async def listar_culturas(sessao: Sessao) -> list[Cultura]:
    return list(await sessao.scalars(select(Cultura).order_by(Cultura.id)))


@router.post("/culturas", response_model=CulturaLer, status_code=status.HTTP_201_CREATED)
async def criar_cultura(dados: CulturaCriar, admin: Administrador, sessao: Sessao) -> Cultura:
    if await sessao.get(Cultura, dados.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cultura já existe")
    cultura = Cultura(**dados.model_dump())
    sessao.add(cultura)
    auditar(sessao, admin, "cultura.criar", "cultura", cultura.id, depois=dados.model_dump())
    await sessao.commit()
    return cultura


@router.put("/culturas/{cultura_id}", response_model=CulturaLer)
async def actualizar_cultura(cultura_id: str, dados: CulturaEscrever, admin: Administrador,
                             sessao: Sessao) -> Cultura:
    cultura = await sessao.get(Cultura, cultura_id)
    if cultura is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura não encontrada")
    antes = instantaneo(cultura, ("nome", "nome_cientifico"))
    for campo, valor in dados.model_dump().items():
        setattr(cultura, campo, valor)
    auditar(sessao, admin, "cultura.actualizar", "cultura", cultura.id, antes=antes, depois=dados.model_dump())
    await sessao.commit()
    return cultura


def _consulta_patologias():
    return select(Patologia).options(selectinload(Patologia.validado_por), selectinload(Patologia.fotos))


def _para_ler(p: Patologia) -> PatologiaLer:
    return PatologiaLer(
        id=p.id, cultura_id=p.cultura_id, codigo=p.codigo, nome_local=p.nome_local,
        nome_cientifico=p.nome_cientifico, tipo=p.tipo, recomendacao=p.recomendacao, sintomas=p.sintomas,
        prevencao=p.prevencao, declaracao_obrigatoria=p.declaracao_obrigatoria, versao_conteudo=p.versao_conteudo,
        validado_por_nome=p.validado_por.nome if p.validado_por else None, validado_em=p.validado_em,
        fotos=[FotoLer(id=f.id, legenda=f.legenda, url=f"/fotos-referencia/{f.id}") for f in p.fotos],
    )


async def _obter(sessao: AsyncSession, patologia_id: int) -> Patologia:
    # populate_existing: recarrega a patologia e as fotos sem expirar o resto da sessão
    # (expirar o utilizador autenticado obrigaria a um carregamento implícito, proibido em async).
    p = await sessao.scalar(_consulta_patologias().where(Patologia.id == patologia_id)
                            .execution_options(populate_existing=True))
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    return p


@router.get("/patologias", response_model=list[PatologiaLer])
async def listar_patologias(sessao: Sessao, cultura: str | None = None) -> list[PatologiaLer]:
    consulta = _consulta_patologias().order_by(Patologia.cultura_id, Patologia.codigo)
    if cultura:
        consulta = consulta.where(Patologia.cultura_id == cultura)
    return [_para_ler(p) for p in await sessao.scalars(consulta)]


@router.post("/patologias", response_model=PatologiaLer, status_code=status.HTTP_201_CREATED)
async def criar_patologia(dados: PatologiaCriar, admin: Administrador, sessao: Sessao) -> PatologiaLer:
    if await sessao.get(Cultura, dados.cultura_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cultura inexistente")
    patologia = Patologia(**dados.model_dump())
    sessao.add(patologia)
    try:
        await sessao.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe essa patologia nesta cultura") from None
    auditar(sessao, admin, "patologia.criar", "patologia", patologia.id,
            depois=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.commit()
    return _para_ler(await _obter(sessao, patologia.id))


@router.put("/patologias/{patologia_id}", response_model=PatologiaLer)
async def actualizar_patologia(patologia_id: int, dados: PatologiaEscrever, admin: Administrador,
                               sessao: Sessao) -> PatologiaLer:
    """Os campos opcionais (sintomas, prevenção, declaração obrigatória) só mudam se forem enviados.

    Mudar o texto que o agricultor lê sobe a versão do conteúdo e retira a validação (o texto
    novo ainda não foi revisto por um técnico).
    """
    patologia = await _obter(sessao, patologia_id)
    antes = instantaneo(patologia, CAMPOS_PATOLOGIA)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(patologia, campo, valor)
    if any(antes[c] != getattr(patologia, c) for c in CAMPOS_TEXTO):
        patologia.versao_conteudo += 1
        patologia.validado_por_id = patologia.validado_em = None
    auditar(sessao, admin, "patologia.actualizar", "patologia", patologia.id, antes=antes,
            depois=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.commit()
    return _para_ler(await _obter(sessao, patologia_id))


@router.post("/patologias/{patologia_id}/validar", response_model=PatologiaLer)
async def validar_conteudo(patologia_id: int, utilizador: Pessoal, sessao: Sessao) -> PatologiaLer:
    """Um técnico ou o administrador confirma que o texto (sintomas, recomendação...) está correcto."""
    patologia = await _obter(sessao, patologia_id)
    patologia.validado_por_id, patologia.validado_em = utilizador.id, datetime.now(timezone.utc)
    auditar(sessao, utilizador, "patologia.validar", "patologia", patologia.id,
            depois={"versao_conteudo": patologia.versao_conteudo})
    await sessao.commit()
    return _para_ler(await _obter(sessao, patologia_id))


@router.post("/patologias/{patologia_id}/fotos", response_model=PatologiaLer, status_code=status.HTTP_201_CREATED)
async def acrescentar_foto(patologia_id: int, admin: Administrador, sessao: Sessao,
                           ficheiro: Annotated[UploadFile, File(description="Fotografia JPEG ou PNG")],
                           legenda: Annotated[str | None, Form(max_length=200)] = None) -> PatologiaLer:
    patologia = await _obter(sessao, patologia_id)
    extensao = {"image/jpeg": ".jpg", "image/png": ".png"}.get(ficheiro.content_type or "")
    if extensao is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "A imagem tem de ser JPEG ou PNG")
    conteudo = await ficheiro.read()
    if len(conteudo) > 5 * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Imagem maior que 5 MB")
    pasta = definicoes.pasta_imagens / "referencia"
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{patologia.cultura_id}_{patologia.codigo}_{uuid.uuid4().hex[:10]}{extensao}"
    (pasta / nome).write_bytes(conteudo)
    sessao.add(FotoReferencia(patologia_id=patologia.id, caminho_ficheiro=nome, legenda=(legenda or "").strip() or None))
    auditar(sessao, admin, "patologia.foto_acrescentar", "patologia", patologia.id, depois={"ficheiro": nome})
    await sessao.commit()
    return _para_ler(await _obter(sessao, patologia_id))


@router.get("/fotos-referencia/{foto_id}", response_class=FileResponse)
async def obter_foto(foto_id: int, sessao: Sessao) -> FileResponse:
    """Pública: a app descarrega as fotos de referência para as mostrar sem rede."""
    foto = await sessao.get(FotoReferencia, foto_id)
    caminho = definicoes.pasta_imagens / "referencia" / foto.caminho_ficheiro if foto else None
    if caminho is None or not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fotografia não encontrada")
    return FileResponse(caminho, headers={"Cache-Control": "public, max-age=86400"})


@router.delete("/fotos-referencia/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar_foto(foto_id: int, admin: Administrador, sessao: Sessao) -> None:
    foto = await sessao.get(FotoReferencia, foto_id)
    if foto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fotografia não encontrada")
    caminho = definicoes.pasta_imagens / "referencia" / foto.caminho_ficheiro
    auditar(sessao, admin, "patologia.foto_apagar", "patologia", foto.patologia_id, antes={"ficheiro": foto.caminho_ficheiro})
    await sessao.delete(foto)
    await sessao.commit()
    caminho.unlink(missing_ok=True)


@router.delete("/patologias/{patologia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar_patologia(patologia_id: int, admin: Administrador, sessao: Sessao) -> None:
    patologia = await sessao.get(Patologia, patologia_id)
    if patologia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    auditar(sessao, admin, "patologia.apagar", "patologia", patologia.id,
            antes=instantaneo(patologia, CAMPOS_PATOLOGIA))
    await sessao.delete(patologia)
    await sessao.commit()
