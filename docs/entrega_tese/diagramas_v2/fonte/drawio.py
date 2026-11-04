"""Gerador mínimo de ficheiros .drawio no estilo dos diagramas do PFC.

Estilo: preto e branco, cabeçalhos em cinzento claro (#F2F2F2), Helvetica, linhas de 2 px.
"""

from xml.sax.saxutils import escape

FONTE = "fontFamily=Helvetica;fontColor=#000000;"
LINHA = "strokeColor=#000000;strokeWidth=2;"
CINZA = "#F2F2F2"


class Diagrama:
    def __init__(self, nome: str, largura: int, altura: int):
        self.nome, self.largura, self.altura = nome, largura, altura
        self.celulas: list[str] = []
        self._n = 0

    def _id(self) -> str:
        self._n += 1
        return f"c{self._n}"

    def _vertice(self, valor: str, estilo: str, x, y, w, h, pai: str = "1", id_: str | None = None) -> str:
        id_ = id_ or self._id()
        self.celulas.append(
            f'<mxCell id="{id_}" value="{escape(valor, {chr(34): "&quot;"})}" style="{estilo}" vertex="1" parent="{pai}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return id_

    def aresta(self, origem: str, destino: str, estilo: str = "", rotulo: str = "", pontos=None,
               saida=None, entrada=None) -> str:
        id_ = self._id()
        extra = ""
        if saida:
            extra += f"exitX={saida[0]};exitY={saida[1]};exitDx=0;exitDy=0;"
        if entrada:
            extra += f"entryX={entrada[0]};entryY={entrada[1]};entryDx=0;entryDy=0;"
        geo = '<mxGeometry relative="1" as="geometry">'
        if pontos:
            geo += '<Array as="points">' + "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in pontos) + "</Array>"
        geo += "</mxGeometry>"
        self.celulas.append(
            f'<mxCell id="{id_}" value="{escape(rotulo)}" style="{LINHA}{FONTE}fontSize=18;html=1;'
            f'labelBackgroundColor=#FFFFFF;{estilo}{extra}" edge="1" parent="1" source="{origem}" target="{destino}">'
            f"{geo}</mxCell>")
        return id_

    # --- Formas -----------------------------------------------------------------------
    def texto(self, valor, x, y, w, h, tamanho=19, negrito=False, italico=False, alinhar="center"):
        estilo_letra = (1 if negrito else 0) + (2 if italico else 0)
        return self._vertice(valor, f"text;html=1;{FONTE}fontSize={tamanho};fontStyle={estilo_letra};"
                             f"align={alinhar};verticalAlign=middle;whiteSpace=wrap;", x, y, w, h)

    def caixa(self, valor, x, y, w, h, tamanho=19, arredondada=False, tracejada=False, cinza=False,
              alinhar="center", vertical="middle", negrito=False):
        estilo = (f"rounded={1 if arredondada else 0};arcSize=12;whiteSpace=wrap;html=1;{FONTE}{LINHA}"
                  f"fillColor={CINZA if cinza else '#FFFFFF'};fontSize={tamanho};align={alinhar};"
                  f"verticalAlign={vertical};spacing=10;fontStyle={1 if negrito else 0};")
        if tracejada:
            estilo += "dashed=1;dashPattern=8 6;fillColor=none;"
        return self._vertice(valor, estilo, x, y, w, h)

    def elipse(self, valor, x, y, w=300, h=86, tamanho=20):
        return self._vertice(valor, f"ellipse;whiteSpace=wrap;html=1;{FONTE}{LINHA}fillColor=#FFFFFF;"
                             f"fontSize={tamanho};spacing=12;", x, y, w, h)

    def actor(self, nome, x, y, abstracto=False):
        return self._vertice(nome, f"shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;"
                             f"{FONTE}{LINHA}fillColor=#FFFFFF;fontSize=20;"
                             f"fontStyle={3 if abstracto else 1};whiteSpace=nowrap;", x, y, 46, 92)

    def classe(self, nome, atributos: list[str], x, y, w, linha=24, estereotipo=None):
        cabeca = 58 if estereotipo else 44
        altura = cabeca + 16 + linha * len(atributos)
        titulo = f"«{estereotipo}»<br><b>{escape(nome)}</b>" if estereotipo else f"<b>{escape(nome)}</b>"
        pai = self._vertice(titulo, f"swimlane;fontStyle=0;childLayout=stackLayout;horizontal=1;startSize={cabeca};"
                            f"horizontalStack=0;resizeParent=1;resizeLast=0;collapsible=0;marginBottom=0;html=1;"
                            f"{FONTE}{LINHA}fillColor={CINZA};swimlaneFillColor=#FFFFFF;fontSize=20;",
                            x, y, w, altura)
        corpo = "<br>".join(escape(a) for a in atributos)
        self._vertice(corpo, f"text;html=1;{FONTE}fontSize=18;align=left;verticalAlign=top;spacingLeft=10;"
                      f"spacingTop=6;whiteSpace=wrap;", 0, cabeca, w, altura - cabeca, pai=pai)
        return pai

    def cilindro(self, valor, x, y, w, h, tamanho=19):
        return self._vertice(valor, f"shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=14;{FONTE}{LINHA}"
                             f"fillColor=#FFFFFF;fontSize={tamanho};", x, y, w, h)

    def losango(self, valor, x, y, w, h, tamanho=15):
        return self._vertice(valor, f"rhombus;whiteSpace=wrap;html=1;{FONTE}{LINHA}fillColor=#FFFFFF;"
                             f"fontSize={tamanho};", x, y, w, h)

    def inicio(self, x, y):
        return self._vertice("", f"ellipse;fillColor=#000000;{LINHA}", x, y, 30, 30)

    def fim(self, x, y):
        return self._vertice("", f"ellipse;html=1;shape=endState;fillColor=#000000;{LINHA}", x, y, 36, 36)

    # --- Diagramas de sequência ------------------------------------------------------
    def lifeline(self, nome, cx, y, altura, w=250, cinza=True):
        return self._vertice(nome, f"shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;"
                             f"container=0;collapsible=0;recursiveResize=0;outlineConnect=0;size=90;{FONTE}{LINHA}"
                             f"fillColor={CINZA if cinza else '#FFFFFF'};fontSize=20;fontStyle=1;dashed=0;",
                             cx - w // 2, y, w, altura)

    def mensagem(self, x1, x2, y, rotulo, resposta=False, rotulo_y=-16):
        """Seta horizontal entre duas lifelines (x1 -> x2) à altura y; tracejada se for resposta."""
        id_ = self._id()
        estilo = ("dashed=1;dashPattern=8 6;endArrow=open;endSize=14;" if resposta
                  else "endArrow=block;endFill=1;endSize=14;")
        self.celulas.append(
            f'<mxCell id="{id_}" value="" style="{LINHA}{estilo}html=1;" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1}" y="{y}" as="sourcePoint"/>'
            f'<mxPoint x="{x2}" y="{y}" as="targetPoint"/></mxGeometry></mxCell>')
        esq, dta = min(x1, x2), max(x1, x2)
        t = self.texto(rotulo, esq - 40, y + rotulo_y - 18, dta - esq + 80, 30, tamanho=18)
        self._fundo_branco(t)

    def auto_mensagem(self, x, y, rotulo, largura=70, altura=40):
        id_ = self._id()
        self.celulas.append(
            f'<mxCell id="{id_}" value="" style="{LINHA}endArrow=block;endFill=1;endSize=14;html=1;rounded=0;" '
            f'edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{x}" y="{y}" as="sourcePoint"/><mxPoint x="{x + 4}" y="{y + altura}" as="targetPoint"/>'
            f'<Array as="points"><mxPoint x="{x + largura}" y="{y}"/><mxPoint x="{x + largura}" y="{y + altura}"/>'
            f'</Array></mxGeometry></mxCell>')
        t = self.texto(rotulo, x + largura + 14, y + altura / 2 - 16, 640, 32, tamanho=18, alinhar="left")
        self._fundo_branco(t)

    def _fundo_branco(self, id_):
        """Fundo branco só atrás das letras (o texto não fica por cima das linhas tracejadas)."""
        self.celulas[-1] = self.celulas[-1].replace('style="text;', 'style="text;labelBackgroundColor=#FFFFFF;', 1)

    def fragmento(self, tipo, guarda, x, y, w, h, separadores=()):
        """Fragmento combinado (opt, alt, loop) com a guarda; separadores = [(y, guarda), ...] para o alt."""
        self._vertice(tipo, f"shape=umlFrame;whiteSpace=wrap;html=1;width=80;height=36;{FONTE}{LINHA}"
                      f"fillColor=none;fontSize=19;fontStyle=1;", x, y, w, h)
        self.texto(f"[{guarda}]", x + 92, y + 2, w - 100, 34, tamanho=18, italico=True, alinhar="left")
        for ys, g in separadores:
            id_ = self._id()
            self.celulas.append(
                f'<mxCell id="{id_}" value="" style="{LINHA}dashed=1;dashPattern=8 6;endArrow=none;html=1;" '
                f'edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x}" y="{ys}" '
                f'as="sourcePoint"/><mxPoint x="{x + w}" y="{ys}" as="targetPoint"/></mxGeometry></mxCell>')
            self.texto(f"[{g}]", x + 12, ys + 4, w - 20, 34, tamanho=18, italico=True, alinhar="left")

    # --- Diagramas de actividades -----------------------------------------------------
    def raia(self, nome, x, y, w, h, cabeca=100):
        self._vertice("", f"rounded=0;html=1;{LINHA}fillColor=none;", x, y, w, h)
        self._vertice(nome, f"rounded=0;whiteSpace=wrap;html=1;{FONTE}{LINHA}fillColor=#FFFFFF;fontSize=21;"
                      f"fontStyle=1;", x, y, w, cabeca)

    def actividade(self, valor, cx, y, w=400, h=96, tamanho=20):
        return self.caixa(valor, cx - w // 2, y, w, h, tamanho=tamanho, arredondada=True)

    def gravar(self, caminho: str) -> None:
        xml = (f'<mxfile host="drawio"><diagram name="{escape(self.nome)}" id="d1">'
               f'<mxGraphModel dx="1600" dy="1200" grid="0" gridSize="10" guides="1" page="1" pageScale="1" '
               f'pageWidth="{self.largura}" pageHeight="{self.altura}" background="#FFFFFF" math="0" shadow="0">'
               f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(self.celulas)}</root>'
               f"</mxGraphModel></diagram></mxfile>")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(xml)


# Estilos de arestas UML
ASSOC = "endArrow=none;"
INCLUDE = "dashed=1;dashPattern=8 6;endArrow=open;endSize=14;"
GENERALIZA = "endArrow=block;endFill=0;endSize=16;"
SETA = "endArrow=block;endFill=1;endSize=12;"
RESPOSTA = "dashed=1;dashPattern=8 6;endArrow=open;endSize=12;"
ORTOGONAL = "edgeStyle=orthogonalEdgeStyle;rounded=0;"
