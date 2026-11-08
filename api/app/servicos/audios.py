"""Áudio em línguas locais (funcionalidade 14): a equipa grava, o agricultor ouve sem rede.

Não há tradução nem voz sintética: cada gravação é a voz de alguém da equipa. As do catálogo só
chegam à app depois de outra pessoa as confirmar (quatro olhos, como o texto do catálogo); as dos
alertas seguem com o alerta. Os ficheiros ficam em <pasta_imagens>/audio.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import definicoes
from ..esquemas import AudioLer, CoberturaAudio, EstadoAudio, LinguaLer, LinhaCobertura, Reproducao
from ..linguas import CODIGOS, LINGUAS, NOMES
from ..regioes import condicao_utilizador_na_zona, zona_de
from ..tabelas import Audio, Patologia, Perfil, Utilizador
from . import alertas
from .auditoria import auditar

# O browser grava em WebM/Opus (Chrome) ou Ogg/Opus (Firefox); um telemóvel costuma dar M4A ou MP3.
EXTENSOES = {
    "audio/webm": ".webm", "audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
    "audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/aac": ".aac",
    "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav",
}
MAX_BYTES = 4 * 1024 * 1024
MAX_DURACAO_S = 150  # o painel pára aos 2 minutos; a folga cobre ficheiros carregados


def pasta():
    return definicoes.pasta_imagens / "audio"


def linguas() -> list[LinguaLer]:
    return [LinguaLer(codigo=l.codigo, nome=l.nome, provincias=list(l.provincias)) for l in LINGUAS]


def validar_lingua(lingua: str | None) -> str | None:
    if lingua is not None and lingua not in CODIGOS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Língua desconhecida: {lingua}")
    return lingua


def para_ler(a: Audio) -> AudioLer:
    return AudioLer(
        id=a.id, lingua=a.lingua, lingua_nome=NOMES.get(a.lingua, a.lingua), url=f"/audios/ficheiros/{a.caminho_ficheiro}",
        tipo_mime=a.tipo_mime, tamanho_bytes=a.tamanho_bytes, duracao_s=a.duracao_s,
        patologia_id=a.patologia_id, alerta_id=a.alerta_id, autor_id=a.autor_id, autor_nome=a.autor.nome, criado_em=a.criado_em,
        validado_por_nome=a.validado_por.nome if a.validado_por else None, validado_em=a.validado_em,
        reproducoes=a.reproducoes)


def consulta():
    return select(Audio).options(selectinload(Audio.autor), selectinload(Audio.validado_por))


async def de_alertas(sessao: AsyncSession, ids: list[int]) -> dict[int, list[AudioLer]]:
    if not ids:
        return {}
    resultado: dict[int, list[AudioLer]] = {}
    for a in await sessao.scalars(consulta().where(Audio.alerta_id.in_(ids)).order_by(Audio.lingua)):
        resultado.setdefault(a.alerta_id, []).append(para_ler(a))
    return resultado


async def listar(sessao: AsyncSession, patologia_id: int | None = None,
                 alerta_id: int | None = None) -> list[AudioLer]:
    c = consulta().order_by(Audio.patologia_id, Audio.alerta_id, Audio.lingua)
    if patologia_id is not None:
        c = c.where(Audio.patologia_id == patologia_id)
    if alerta_id is not None:
        c = c.where(Audio.alerta_id == alerta_id)
    if patologia_id is None and alerta_id is None:
        c = c.where(Audio.patologia_id.is_not(None))  # o catálogo; os dos alertas vêm com cada alerta
    return [para_ler(a) for a in await sessao.scalars(c)]


async def _obter(sessao: AsyncSession, audio_id: int) -> Audio:
    a = await sessao.scalar(consulta().where(Audio.id == audio_id).execution_options(populate_existing=True))
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gravação não encontrada")
    return a


async def gravar(sessao: AsyncSession, u: Utilizador, ficheiro: UploadFile, lingua: str,
                 duracao_s: float | None, *, patologia_id: int | None = None,
                 alerta_id: int | None = None) -> AudioLer:
    """Guarda a gravação; se já havia uma nesta língua para o mesmo conteúdo, substitui-a."""
    validar_lingua(lingua)
    if patologia_id is not None:
        if await sessao.get(Patologia, patologia_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Patologia não encontrada")
    else:
        await alertas.gerivel(sessao, u, alerta_id, "juntar áudio a este alerta")
    tipo = (ficheiro.content_type or "").split(";")[0].strip().lower()
    extensao = EXTENSOES.get(tipo)
    if extensao is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            "O áudio tem de ser WebM, Ogg, MP3, M4A, AAC ou WAV")
    conteudo = await ficheiro.read()
    if not conteudo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A gravação está vazia")
    if len(conteudo) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Gravação maior que 4 MB")
    if duracao_s is not None and not 0 < duracao_s <= MAX_DURACAO_S:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A gravação tem de durar até 2 minutos")

    alvo = Audio.patologia_id == patologia_id if patologia_id is not None else Audio.alerta_id == alerta_id
    antiga = await sessao.scalar(select(Audio).where(alvo, Audio.lingua == lingua))
    if antiga is not None:
        (pasta() / antiga.caminho_ficheiro).unlink(missing_ok=True)
        await sessao.delete(antiga)
        await sessao.flush()
    pasta().mkdir(parents=True, exist_ok=True)
    prefixo = f"p{patologia_id}" if patologia_id is not None else f"a{alerta_id}"
    nome = f"{prefixo}_{lingua}_{uuid.uuid4().hex[:10]}{extensao}"
    (pasta() / nome).write_bytes(conteudo)
    audio = Audio(patologia_id=patologia_id, alerta_id=alerta_id, lingua=lingua, caminho_ficheiro=nome,
                  tipo_mime=tipo, tamanho_bytes=len(conteudo), duracao_s=duracao_s, autor_id=u.id)
    if alerta_id is not None:  # vai com o alerta: quem o envia responde por ele
        audio.validado_por_id, audio.validado_em = u.id, datetime.now(timezone.utc)
    sessao.add(audio)
    await sessao.flush()
    entidade, entidade_id = ("patologia", patologia_id) if patologia_id is not None else ("alerta", alerta_id)
    auditar(sessao, u, "audio.gravar", entidade, entidade_id,
            antes={"ficheiro": antiga.caminho_ficheiro} if antiga else None,
            depois={"lingua": lingua, "ficheiro": nome, "bytes": len(conteudo)})
    await sessao.commit()
    return para_ler(await _obter(sessao, audio.id))


async def validar(sessao: AsyncSession, u: Utilizador, audio_id: int) -> AudioLer:
    a = await _obter(sessao, audio_id)
    if a.patologia_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "O áudio de um alerta não precisa de validação")
    if a.autor_id == u.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Outra pessoa da equipa tem de confirmar que a gravação diz o mesmo que o texto")
    a.validado_por_id, a.validado_em = u.id, datetime.now(timezone.utc)
    auditar(sessao, u, "audio.validar", "patologia", a.patologia_id, depois={"audio_id": a.id, "lingua": a.lingua})
    await sessao.commit()
    return para_ler(await _obter(sessao, audio_id))


async def apagar(sessao: AsyncSession, u: Utilizador, audio_id: int) -> None:
    a = await _obter(sessao, audio_id)
    if a.alerta_id is not None:
        await alertas.gerivel(sessao, u, a.alerta_id, "apagar o áudio deste alerta")
    entidade, entidade_id = ("patologia", a.patologia_id) if a.patologia_id is not None else ("alerta", a.alerta_id)
    auditar(sessao, u, "audio.apagar", entidade, entidade_id, antes={"lingua": a.lingua, "ficheiro": a.caminho_ficheiro})
    ficheiro = pasta() / a.caminho_ficheiro
    await sessao.delete(a)
    await sessao.commit()
    ficheiro.unlink(missing_ok=True)


async def caminho(sessao: AsyncSession, nome: str):
    """Pelo nome do ficheiro (único): uma gravação nova tem sempre outro nome, e a app guarda-as por ele."""
    a = await sessao.scalar(select(Audio).where(Audio.caminho_ficheiro == nome))
    ficheiro = pasta() / a.caminho_ficheiro if a else None
    if ficheiro is None or not ficheiro.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gravação não encontrada")
    return ficheiro, a.tipo_mime


async def registar_reproducoes(sessao: AsyncSession, lista: list[Reproducao]) -> None:
    """A app conta as vezes que cada gravação foi ouvida (mesmo sem rede) e envia na sincronização."""
    for r in lista[:500]:
        await sessao.execute(update(Audio).where(Audio.id == r.audio_id).values(reproducoes=Audio.reproducoes + r.vezes))
    await sessao.commit()


async def cobertura(sessao: AsyncSession, u: Utilizador) -> CoberturaAudio:
    """Que pragas já têm gravação em cada língua, e que línguas escolheram os agricultores da zona."""
    patologias = list(await sessao.scalars(select(Patologia).order_by(Patologia.cultura_id, Patologia.codigo)))
    estados: dict[int, dict[str, EstadoAudio]] = {}
    por_validar = 0
    for a in await sessao.scalars(select(Audio).where(Audio.patologia_id.is_not(None))):
        estados.setdefault(a.patologia_id, {})[a.lingua] = EstadoAudio(id=a.id, validado=a.validado_em is not None)
        por_validar += a.validado_em is None
    contagem = dict((await sessao.execute(
        select(Utilizador.lingua, func.count()).where(
            Utilizador.perfil == Perfil.AGRICULTOR, Utilizador.activo.is_(True),
            condicao_utilizador_na_zona(zona_de(u))).group_by(Utilizador.lingua))).all())
    return CoberturaAudio(
        linguas=linguas(),
        patologias=[LinhaCobertura(patologia_id=p.id, cultura_id=p.cultura_id, codigo=p.codigo, nome=p.nome_local,
                                   tipo=p.tipo, audios=estados.get(p.id, {})) for p in patologias],
        agricultores_por_lingua={k: v for k, v in contagem.items() if k},
        agricultores_sem_lingua=contagem.get(None, 0),
        por_validar=por_validar,
    )
