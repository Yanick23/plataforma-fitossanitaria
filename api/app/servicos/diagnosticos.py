"""Diagnósticos: quem pode ver o quê e como se apresentam."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..esquemas import DiagnosticoAdminLer, DiagnosticoLer
from ..regioes import zona_de
from ..repositorios.diagnosticos import estado_validacao
from ..seguranca import pseudonimo
from ..tabelas import Diagnostico, Patologia, Perfil, Utilizador


async def mapa_patologias(sessao: AsyncSession) -> dict[tuple[str, str], Patologia]:
    return {(p.cultura_id, p.codigo): p for p in await sessao.scalars(select(Patologia))}


def para_ler(d: Diagnostico, anonimo: bool = False) -> DiagnosticoLer:
    v = d.validacao
    return DiagnosticoLer(
        id=d.id, utilizador_id=0 if anonimo else d.utilizador_id, cultura_id=d.cultura_id,
        classe_prevista=d.classe_prevista, confianca=d.confianca, data=d.data,
        versao_modelo=d.versao_modelo, tempo_inferencia_ms=d.tempo_inferencia_ms,
        tem_imagem=d.imagem is not None, validacao=estado_validacao(d).value,
        classe_confirmada=v.classe_confirmada if v else None, nota_tecnico=v.nota if v else None,
        seguimento_respondido=d.seguimento is not None,
    )


def para_admin(d: Diagnostico, patologias: dict[tuple[str, str], Patologia],
               anonimo: bool = False) -> DiagnosticoAdminLer:
    """anonimo=True (investigador): pseudónimo em vez do nome, sem telefone nem id do agricultor."""
    p = patologias.get((d.cultura_id, d.classe_prevista))
    v = d.validacao
    return DiagnosticoAdminLer(
        **para_ler(d, anonimo).model_dump(),
        utilizador_nome=pseudonimo(d.utilizador_id) if anonimo else d.utilizador.nome,
        utilizador_telefone="" if anonimo else d.utilizador.telefone,
        distrito_id=d.distrito_id, distrito_nome=d.distrito.nome if d.distrito else None,
        provincia_codigo=d.distrito.provincia_codigo if d.distrito else None,
        patologia_nome=p.nome_local if p else None, tipo=p.tipo if p else None,
        tecnico_nome=v.tecnico.nome if v and v.tecnico else None,
        validado_em=v.actualizado_em if v else None,
    )


def pode_ver(utilizador: Utilizador, d: Diagnostico) -> bool:
    """Dono, administrador, investigador (só leitura), ou técnico/coordenador cuja zona inclui o diagnóstico."""
    if d.utilizador_id == utilizador.id or utilizador.perfil in (Perfil.ADMINISTRADOR, Perfil.INVESTIGADOR):
        return True
    if utilizador.perfil not in (Perfil.TECNICO, Perfil.COORDENADOR):
        return False
    zona = zona_de(utilizador)
    if zona.distrito_id:
        return d.distrito_id == zona.distrito_id
    if zona.provincia_codigo:
        return d.distrito is not None and d.distrito.provincia_codigo == zona.provincia_codigo
    return zona.area_texto is not None and d.utilizador.area == zona.area_texto
