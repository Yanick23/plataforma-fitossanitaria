"""Línguas locais e áudio (funcionalidade 14): gravar, validar, ouvir e ver o que falta gravar."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import AudioLer, CoberturaAudio, LinguaLer, Reproducao
from ..seguranca import Leitor, Pessoal, UtilizadorActual
from ..servicos import audios as servico

router = APIRouter(tags=["Línguas locais e áudio"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]
Ficheiro = Annotated[UploadFile, File(description="Gravação: WebM, Ogg, MP3, M4A, AAC ou WAV, até 4 MB")]
Lingua = Annotated[str, Form(pattern=r"^[a-z]{3}$", description="Código ISO 639-3, ver GET /linguas")]
Duracao = Annotated[float | None, Form(description="Duração em segundos (até 2 minutos)")]


@router.get("/linguas", response_model=list[LinguaLer])
async def linguas() -> list[LinguaLer]:
    """Pública: a app mostra-as no registo, sem sessão."""
    return servico.linguas()


@router.get("/audios", response_model=list[AudioLer])
async def listar(utilizador: Leitor, sessao: Sessao, patologia_id: int | None = None,
                 alerta_id: int | None = None) -> list[AudioLer]:
    """Para o painel: inclui as gravações do catálogo ainda por validar."""
    return await servico.listar(sessao, patologia_id, alerta_id)


@router.get("/audios/cobertura", response_model=CoberturaAudio)
async def cobertura(utilizador: Leitor, sessao: Sessao) -> CoberturaAudio:
    return await servico.cobertura(sessao, utilizador)


@router.post("/patologias/{patologia_id}/audios", response_model=AudioLer, status_code=status.HTTP_201_CREATED)
async def gravar_patologia(patologia_id: int, utilizador: Pessoal, sessao: Sessao, ficheiro: Ficheiro,
                           lingua: Lingua, duracao_s: Duracao = None) -> AudioLer:
    """A recomendação de uma praga ou doença, lida numa língua. Fica por validar."""
    return await servico.gravar(sessao, utilizador, ficheiro, lingua, duracao_s, patologia_id=patologia_id)


@router.post("/alertas/{alerta_id}/audios", response_model=AudioLer, status_code=status.HTTP_201_CREATED)
async def gravar_alerta(alerta_id: int, utilizador: Pessoal, sessao: Sessao, ficheiro: Ficheiro,
                        lingua: Lingua, duracao_s: Duracao = None) -> AudioLer:
    """Mensagem de voz de um alerta (o autor, o coordenador da província ou o administrador)."""
    return await servico.gravar(sessao, utilizador, ficheiro, lingua, duracao_s, alerta_id=alerta_id)


@router.post("/audios/{audio_id}/validar", response_model=AudioLer)
async def validar(audio_id: int, utilizador: Pessoal, sessao: Sessao) -> AudioLer:
    """Outra pessoa da equipa confirma que a gravação diz o mesmo que o texto do catálogo."""
    return await servico.validar(sessao, utilizador, audio_id)


@router.delete("/audios/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def apagar(audio_id: int, utilizador: Pessoal, sessao: Sessao) -> None:
    await servico.apagar(sessao, utilizador, audio_id)


@router.get("/audios/ficheiros/{nome}", response_class=FileResponse)
async def ficheiro(nome: str, sessao: Sessao) -> FileResponse:
    """Pública, como as fotos de referência: a app descarrega-a e o painel toca-a num <audio>."""
    caminho, tipo = await servico.caminho(sessao, nome)
    return FileResponse(caminho, media_type=tipo, headers={"Cache-Control": "public, max-age=86400"})


@router.post("/audios/reproducoes", status_code=status.HTTP_204_NO_CONTENT)
async def reproducoes(lista: list[Reproducao], utilizador: UtilizadorActual, sessao: Sessao) -> None:
    """A app envia, na sincronização, quantas vezes cada gravação foi ouvida."""
    await servico.registar_reproducoes(sessao, lista)
