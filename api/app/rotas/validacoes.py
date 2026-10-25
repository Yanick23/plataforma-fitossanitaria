"""Validação dos diagnósticos pelo técnico, exactidão em campo e exportação para retreino."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import obter_sessao
from ..esquemas import DiagnosticoAdminLer, ExactidaoCampo, ValidacaoEscrever
from ..seguranca import Administrador, Pessoal
from ..servicos import validacoes as servico
from ..servicos.diagnosticos import mapa_patologias, para_admin
from .diagnosticos import _obter

router = APIRouter(tags=["Validação"])
Sessao = Annotated[AsyncSession, Depends(obter_sessao)]


@router.put("/diagnosticos/{diagnostico_id}/validacao", response_model=DiagnosticoAdminLer)
async def validar(diagnostico_id: UUID, dados: ValidacaoEscrever, utilizador: Pessoal,
                  sessao: Sessao) -> DiagnosticoAdminLer:
    """O técnico confirma a classe do modelo ou corrige-a (e pode deixar uma nota ao agricultor)."""
    await servico.validar(sessao, utilizador, await _obter(sessao, diagnostico_id), dados)
    sessao.expire_all()
    return para_admin(await _obter(sessao, diagnostico_id), await mapa_patologias(sessao))


@router.get("/validacoes/exactidao", response_model=ExactidaoCampo)
async def exactidao(utilizador: Pessoal, sessao: Sessao, cultura: str | None = None,
                    desde: datetime | None = None) -> ExactidaoCampo:
    """Concordância modelo × técnico na zona de quem pede: a exactidão do modelo no terreno."""
    return await servico.exactidao(sessao, utilizador, cultura, desde)


@router.get("/validacoes/exportar", response_class=Response,
            responses={200: {"content": {"application/zip": {}}}})
async def exportar(_: Administrador, sessao: Sessao) -> Response:
    """ZIP com as fotografias validadas e rotulos.csv, para retreinar o modelo no Colab."""
    conteudo = await servico.exportar_validados(sessao)
    return Response(conteudo, media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="validados.zip"'})
