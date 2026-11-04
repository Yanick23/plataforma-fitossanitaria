"""D2 — Diagrama de classes da plataforma (versão 2), a partir de api/app/tabelas.py."""

import sys

from drawio import ASSOC, ORTOGONAL, Diagrama

d = Diagrama("Classes", 3180, 1800)
C = [40, 580, 1120, 1660, 2200, 2760]   # colunas
R = [40, 520, 990, 1420]          # linhas
W = 380

COMPOSICAO = "endArrow=none;startArrow=diamondThin;startFill=1;startSize=22;"


def rel(a, b, ma, mb, rotulo="", estilo=ASSOC, **kw):
    """Associação com multiplicidades nas pontas (ma junto de a, mb junto de b)."""
    e = d.aresta(a, b, estilo, rotulo, **kw)
    for valor, x in ((ma, -0.85), (mb, 0.85)):
        d.celulas.append(
            f'<mxCell id="{e}_{x}" value="{valor}" style="edgeLabel;html=1;fontFamily=Helvetica;fontSize=17;'
            f'labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" parent="{e}">'
            f'<mxGeometry x="{x}" y="-14" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')
    return e


# Linha 1: catálogo e modelos
modelo = d.classe("ModeloML", ["- versao: int", "- classes: List<String>", "- acuraciaTeste: double",
                               "- sha256: String", "- estado: EstadoModelo",
                               "- distritosPiloto: List<Distrito>"], C[0], R[0], W)
cultura = d.classe("Cultura", ["- id: String", "- nome: String", "- nomeCientifico: String"], C[1], R[0], W)
patologia = d.classe("Patologia", ["- codigo: String", "- nomeLocal: String", "- nomeCientifico: String",
                                   "- tipo: TipoPatologia", "- recomendacao: String", "- sintomas: String",
                                   "- prevencao: String", "- declaracaoObrigatoria: bool",
                                   "- versaoConteudo: int"], C[2], R[0], W)
foto = d.classe("FotoReferencia", ["- caminhoFicheiro: String", "- legenda: String"], C[3], R[0], W)
d.classe("TipoPatologia", ["DOENCA", "PRAGA", "SAUDAVEL"], C[4], R[0], W, estereotipo="enumeration")

# Linha 2: diagnóstico e o que dele decorre
leitura = d.classe("AlertaLeitura", ["- lidoEm: DateTime"], C[0], R[1], W)
alerta = d.classe("Alerta", ["- titulo: String", "- mensagem: String", "- nivel: NivelAlerta",
                             "- expiraEm: DateTime", "- arquivado: bool"], C[1], R[1], W)
diag = d.classe("Diagnostico", ["- id: UUID", "- data: DateTime", "- classePrevista: String",
                                "- confianca: double", "- versaoModelo: int"], C[2], R[1], W)
imagem = d.classe("Imagem", ["- caminhoFicheiro: String", "- dataCaptura: DateTime"], C[3], R[1], W)
seguimento = d.classe("Seguimento", ["- seguiu: Seguiu", "- resultado: ResultadoTratamento",
                                     "- comentario: String"], C[4], R[1], W)

# Linha 3: zonas, pessoas e trabalho do técnico
provincia = d.classe("Provincia", ["- codigo: String (ISO 3166-2)", "- nome: String"], C[0], R[2], W)
distrito = d.classe("Distrito", ["- id: int", "- nome: String"], C[1], R[2], W)
utilizador = d.classe("Utilizador", ["- id: int", "- nome: String", "- telefone: String",
                                     "- perfil: Perfil", "- activo: bool"], C[2], R[2], W)
validacao = d.classe("Validacao", ["- classeConfirmada: String", "- correcto: bool", "- nota: String"],
                     C[3], R[2], W)
visita = d.classe("PedidoVisita", ["- estado: EstadoVisita", "- mensagem: String", "- dataAgendada: DateTime",
                                   "- notasTecnico: String"], C[4], R[2], W)

# Linha 4: suporte
previsao = d.classe("PrevisaoMeteo", ["- obtidaEm: DateTime", "- dados: JSON (horária, 7 dias)"], C[0], R[3], W)
d.classe("Perfil", ["AGRICULTOR", "TECNICO", "COORDENADOR", "INVESTIGADOR", "ADMINISTRADOR"],
         C[1], R[3], W, estereotipo="enumeration")
notif = d.classe("Notificacao", ["- tipo: String", "- titulo: String", "- mensagem: String", "- lidaEm: DateTime"],
                 C[2], R[3], W)
auditoria = d.classe("RegistoAuditoria", ["- accao: String", "- entidade: String",
                                          "- detalhes: JSON (antes e depois)", "- criadoEm: DateTime"], C[3], R[3], W)
d.classe("EstadoVisita", ["PENDENTE", "AGENDADA", "RESOLVIDA", "CANCELADA"], C[4], R[3], W,
         estereotipo="enumeration")

# Restantes enumerados (coluna da direita)
d.classe("EstadoModelo", ["PILOTO", "PUBLICADO", "RETIRADO"], C[5], R[0], W, estereotipo="enumeration")
d.classe("NivelAlerta", ["INFORMACAO", "AVISO", "URGENTE"], C[5], R[1], W, estereotipo="enumeration")
d.classe("Seguiu", ["SIM", "PARCIAL", "NAO"], C[5], R[2], W, estereotipo="enumeration")
d.classe("ResultadoTratamento", ["MELHOROU", "IGUAL", "PIOROU", "NAO_SEI"], C[5], R[3], W,
         estereotipo="enumeration")

# Relações
rel(cultura, patologia, "1", "1..*", "contém", COMPOSICAO)
rel(patologia, foto, "1", "0..*", "ilustrada por", COMPOSICAO)
rel(cultura, modelo, "1", "0..*", "tem")
rel(diag, patologia, "0..*", "1", "classe prevista")
rel(utilizador, diag, "1", "0..*", "efectua")
rel(diag, imagem, "1", "0..1", "analisa", COMPOSICAO)
rel(diag, seguimento, "1", "0..1", "", COMPOSICAO + ORTOGONAL, saida=(0.85, 1), entrada=(0.5, 1),
    pontos=[(1443, 830), (2390, 830)])
rel(diag, validacao, "1", "0..1", "", COMPOSICAO + ORTOGONAL, saida=(0.75, 1), entrada=(0.5, 0),
    pontos=[(1405, 955), (1850, 955)])
rel(utilizador, validacao, "1", "0..*", "valida")
rel(diag, visita, "1", "0..*", "origina", ASSOC + ORTOGONAL, saida=(0.95, 1), entrada=(0.5, 0),
    pontos=[(1481, 920), (2390, 920)])
rel(diag, distrito, "0..*", "0..1", "ocorre em")
rel(provincia, distrito, "1", "1..*", "", COMPOSICAO)
rel(distrito, utilizador, "0..1", "0..*", "pertence a")
rel(alerta, distrito, "0..*", "0..1", "destino")
rel(alerta, provincia, "0..*", "0..1", "destino")
rel(alerta, patologia, "0..*", "0..1", "sobre")
rel(leitura, alerta, "0..*", "1", "regista")
rel(notif, utilizador, "0..*", "1", "destinatário")
rel(auditoria, utilizador, "0..*", "0..1", "autor")
rel(previsao, distrito, "0..1", "1", "prevê")

d.gravar(sys.argv[1])
