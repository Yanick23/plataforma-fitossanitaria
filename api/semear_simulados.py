"""Dados SIMULADOS para demonstrar a Vigilância (mapa, tendência, surtos, eficácia).

Cria agricultores fictícios em 8 distritos e ~8 semanas de diagnósticos, com dois picos
para disparar sinais de surto:
  - lagarta-do-funil (milho) em Boane, nos últimos 7 dias  -> sinal URGENTE (subida >= 4x)
  - mosaico (mandioca) em Chókwè, nos últimos 7 dias        -> sinal AVISO   (subida >= 2x)
Também cria validações do técnico e respostas de seguimento (eficácia das recomendações).

Tudo o que é simulado fica identificado:
  - agricultores com telefone 8900000NN (prefixo 89 não existe em Moçambique: nenhum SMS sai)
    e nome a começar por "SIM ";
  - diagnósticos, validações e seguimentos pertencem a esses agricultores.
Para apagar tudo:  --apagar

Uso (no servidor, com os contentores a correr; o script não está na imagem, vai por stdin):
    docker exec -i agrodiagnostico-api python - < semear_simulados.py            # criar
    docker exec -i agrodiagnostico-api python - --apagar < semear_simulados.py   # apagar
Volta a correr = apaga os simulados anteriores e cria de novo (as datas acompanham o dia de hoje).
"""

import asyncio
import random
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.database import SessaoLocal
from app.regioes import distrito_por_nome
from app.seguranca import gerar_hash
from app.tabelas import (AlertaLeitura, Diagnostico, EnvioSMS, Imagem, Notificacao, PedidoVisita, Perfil,
                         ResultadoTratamento, Seguimento, Seguiu, Utilizador, Validacao)

PREFIXO_TEL = "8900000"
SEMENTE = 2026

MILHO = ["besouro_da_folha", "gafanhoto", "lagarta_do_cartucho", "listrado_do_milho", "mancha_da_folha",
         "queima_da_folha", "saudavel"]
MANDIOCA = ["acaro_verde", "mancha_bacteriana", "mancha_castanha", "mosaico", "saudavel"]

# distrito -> (agricultores, diagnósticos por semana na base, peso do milho)
DISTRITOS = {
    "Boane": (2, 3, 0.8),
    "Marracuene": (1, 2, 0.6),
    "Manhiça": (1, 2, 0.5),
    "Moamba": (1, 1, 0.7),
    "Chokwe": (2, 3, 0.4),
    "Bilene": (1, 1, 0.5),
    "Gurue": (1, 2, 0.6),
    "Angonia": (1, 2, 0.9),
}
# Picos nos últimos 7 dias: (distrito, cultura, classe, casos)
# (distrito, cultura, classe, casos nos últimos 7 dias, casos por semana nas 4 semanas anteriores)
PICOS = [("Boane", "milho", "lagarta_do_cartucho", 9, 1),   # 9 contra média 1 -> 9x  -> URGENTE
         ("Chokwe", "mandioca", "mosaico", 5, 2)]           # 5 contra média 2 -> 2,5x -> AVISO
LINGUAS = ["pt", "vmw", "ts", "ngl", "seh", "ny"]


async def apagar(sessao) -> int:
    ids_u = list(await sessao.scalars(select(Utilizador.id).where(Utilizador.telefone.like(PREFIXO_TEL + "%"))))
    if not ids_u:
        return 0
    ids_d = select(Diagnostico.id).where(Diagnostico.utilizador_id.in_(ids_u))
    for tabela, coluna in ((Seguimento, Seguimento.diagnostico_id), (Validacao, Validacao.diagnostico_id),
                           (Notificacao, Notificacao.diagnostico_id), (PedidoVisita, PedidoVisita.diagnostico_id),
                           (Imagem, Imagem.diagnostico_id)):
        await sessao.execute(delete(tabela).where(coluna.in_(ids_d)))
    await sessao.execute(delete(AlertaLeitura).where(AlertaLeitura.utilizador_id.in_(ids_u)))
    await sessao.execute(delete(EnvioSMS).where(EnvioSMS.utilizador_id.in_(ids_u)))
    await sessao.execute(delete(Notificacao).where(Notificacao.utilizador_id.in_(ids_u)))
    await sessao.execute(delete(Diagnostico).where(Diagnostico.utilizador_id.in_(ids_u)))
    await sessao.execute(delete(Utilizador).where(Utilizador.id.in_(ids_u)))
    return len(ids_u)


def confianca(rng: random.Random) -> float:
    return round(rng.uniform(0.38, 0.6) if rng.random() < 0.12 else rng.uniform(0.6, 0.995), 3)


async def criar(sessao) -> None:
    rng = random.Random(SEMENTE)
    agora = datetime.now(timezone.utc)
    tecnico = await sessao.scalar(select(Utilizador).where(
        Utilizador.perfil.in_([Perfil.TECNICO, Perfil.ADMINISTRADOR])).order_by(Utilizador.perfil, Utilizador.id))
    hash_inutil = gerar_hash(secrets.token_urlsafe(24))  # ninguém entra com estas contas

    agricultores: dict[str, list[Utilizador]] = {}
    n = 1
    for nome_d, (quantos, _, _) in DISTRITOS.items():
        d = await distrito_por_nome(sessao, nome_d)
        if d is None:
            print(f"Distrito não encontrado: {nome_d}; ignorado")
            continue
        agricultores[nome_d] = []
        for _ in range(quantos):
            u = Utilizador(nome=f"SIM Agricultor {n:02d} ({d.nome})", telefone=f"{PREFIXO_TEL}{n:02d}",
                           hash_palavra_passe=hash_inutil, perfil=Perfil.AGRICULTOR, area=d.nome,
                           distrito_id=d.id, provincia_codigo=d.provincia_codigo, lingua=rng.choice(LINGUAS),
                           criado_em=agora - timedelta(days=60))
            sessao.add(u)
            agricultores[nome_d].append(u)
            n += 1
    await sessao.flush()

    diagnosticos: list[Diagnostico] = []

    def novo(u: Utilizador, cultura: str, classe: str, quando: datetime) -> None:
        d = Diagnostico(id=str(uuid.uuid4()), utilizador_id=u.id, cultura_id=cultura, classe_prevista=classe,
                        confianca=confianca(rng), data=quando, versao_modelo=1,
                        tempo_inferencia_ms=rng.randint(140, 260), recebido_em=quando + timedelta(minutes=rng.randint(1, 600)),
                        distrito_id=u.distrito_id)
        sessao.add(d)
        diagnosticos.append(d)

    # Base: 8 semanas, ritmo estável por distrito (35% folhas saudáveis)
    for nome_d, (_, por_semana, peso_milho) in DISTRITOS.items():
        for semana in range(8):
            for _ in range(max(0, por_semana + rng.choice([-1, 0, 0, 1]))):
                cultura = "milho" if rng.random() < peso_milho else "mandioca"
                classes = MILHO if cultura == "milho" else MANDIOCA
                classe = "saudavel" if rng.random() < 0.35 else rng.choice([c for c in classes if c != "saudavel"])
                quando = agora - timedelta(days=7 * semana + rng.uniform(0, 7), hours=rng.uniform(0, 10))
                if (nome_d, cultura, classe) in {(p[0], p[1], p[2]) for p in PICOS} and quando > agora - timedelta(days=35):
                    classe = "saudavel"  # a base das classes com pico é controlada abaixo
                novo(rng.choice(agricultores[nome_d]), cultura, classe, quando)

    # Picos: base fixa nas 4 semanas anteriores + casos nos últimos 7 dias
    for nome_d, cultura, classe, casos, por_semana_base in PICOS:
        for semana in range(1, 5):
            for _ in range(por_semana_base):
                novo(rng.choice(agricultores[nome_d]), cultura, classe,
                     agora - timedelta(days=7 * semana + rng.uniform(0.5, 6.5)))
        for _ in range(casos):
            novo(rng.choice(agricultores[nome_d]), cultura, classe, agora - timedelta(days=rng.uniform(0.2, 6.5)))
    await sessao.flush()

    # Validações do técnico (40% dos que têm mais de 2 dias): 85% confirmados, resto corrigidos
    validados = 0
    if tecnico:
        for d in diagnosticos:
            if d.data < agora - timedelta(days=2) and rng.random() < 0.4:
                classes = MILHO if d.cultura_id == "milho" else MANDIOCA
                certa = d.classe_prevista if rng.random() < 0.85 else rng.choice(
                    [c for c in classes if c != d.classe_prevista])
                sessao.add(Validacao(diagnostico_id=d.id, tecnico_id=tecnico.id, classe_confirmada=certa,
                                     correcto=certa == d.classe_prevista,
                                     nota="Simulado" if certa == d.classe_prevista else "Simulado: corrigido",
                                     criado_em=d.data + timedelta(days=1), actualizado_em=d.data + timedelta(days=1)))
                validados += 1

    # Seguimentos (eficácia): 45% das pragas/doenças entre 5 e 30 dias
    seguimentos = 0
    for d in diagnosticos:
        if d.classe_prevista != "saudavel" and agora - timedelta(days=30) < d.data < agora - timedelta(days=5) \
                and rng.random() < 0.45:
            seguiu = rng.choices([Seguiu.SIM, Seguiu.PARCIAL, Seguiu.NAO], [6, 3, 2])[0]
            pesos = [7, 2, 1, 1] if seguiu == Seguiu.SIM else [4, 4, 1, 1] if seguiu == Seguiu.PARCIAL else [1, 4, 4, 2]
            resultado = rng.choices([ResultadoTratamento.MELHOROU, ResultadoTratamento.IGUAL,
                                     ResultadoTratamento.PIOROU, ResultadoTratamento.NAO_SEI], pesos)[0]
            sessao.add(Seguimento(diagnostico_id=d.id, seguiu=seguiu, resultado=resultado,
                                  respondido_em=d.data + timedelta(days=rng.randint(4, 7))))
            seguimentos += 1

    total_ag = sum(len(v) for v in agricultores.values())
    print(f"Criados: {total_ag} agricultores SIM, {len(diagnosticos)} diagnósticos, "
          f"{validados} validações, {seguimentos} seguimentos.")


async def principal() -> None:
    so_apagar = "--apagar" in sys.argv
    async with SessaoLocal() as sessao:
        removidos = await apagar(sessao)
        if removidos:
            print(f"Apagados {removidos} agricultores simulados e os seus registos.")
        if not so_apagar:
            await criar(sessao)
        await sessao.commit()


asyncio.run(principal())
