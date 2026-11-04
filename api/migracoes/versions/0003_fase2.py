"""Fase 2: catálogo enriquecido (sintomas, prevenção, fotos, validação do conteúdo, declaração
obrigatória), modelos em piloto por distrito e seguimento do tratamento.

Revisão: 0003
Anterior: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

estado_modelo = sa.Enum("PILOTO", "PUBLICADO", "RETIRADO", name="estado_modelo")
seguiu = sa.Enum("SIM", "PARCIAL", "NAO", name="seguiu")
resultado = sa.Enum("MELHOROU", "IGUAL", "PIOROU", "NAO_SEI", name="resultado_tratamento")
DATA = sa.DateTime(timezone=True)


def upgrade() -> None:
    with op.batch_alter_table("patologias") as t:
        t.add_column(sa.Column("sintomas", sa.Text))
        t.add_column(sa.Column("prevencao", sa.Text))
        t.add_column(sa.Column("declaracao_obrigatoria", sa.Boolean, nullable=False, server_default=sa.false()))
        t.add_column(sa.Column("versao_conteudo", sa.Integer, nullable=False, server_default="1"))
        t.add_column(sa.Column("validado_por_id", sa.Integer,
                               sa.ForeignKey("utilizadores.id", name="fk_patologias_validado_por")))
        t.add_column(sa.Column("validado_em", DATA))

    op.create_table(
        "fotos_referencia",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patologia_id", sa.Integer, sa.ForeignKey("patologias.id", ondelete="CASCADE"), nullable=False),
        sa.Column("caminho_ficheiro", sa.String(300), nullable=False),
        sa.Column("legenda", sa.String(200)),
        sa.Column("criado_em", DATA, nullable=False),
    )
    op.create_index("ix_fotos_referencia_patologia_id", "fotos_referencia", ["patologia_id"])

    estado_modelo.create(op.get_bind(), checkfirst=True)
    with op.batch_alter_table("modelos_ml") as t:
        t.add_column(sa.Column("estado", estado_modelo, nullable=False, server_default="PUBLICADO"))
        t.add_column(sa.Column("distritos_piloto", sa.Text))
        t.add_column(sa.Column("notas", sa.Text))

    op.create_table(
        "seguimentos",
        sa.Column("diagnostico_id", sa.String(36), sa.ForeignKey("diagnosticos.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("seguiu", seguiu, nullable=False),
        sa.Column("resultado", resultado, nullable=False),
        sa.Column("comentario", sa.Text),
        sa.Column("respondido_em", DATA, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("seguimentos")
    with op.batch_alter_table("modelos_ml") as t:
        for coluna in ("notas", "distritos_piloto", "estado"):
            t.drop_column(coluna)
    op.drop_table("fotos_referencia")
    with op.batch_alter_table("patologias") as t:
        t.drop_constraint("fk_patologias_validado_por", type_="foreignkey")
        for coluna in ("validado_em", "validado_por_id", "versao_conteudo", "declaracao_obrigatoria",
                       "prevencao", "sintomas"):
            t.drop_column(coluna)
    for tipo in (resultado, seguiu, estado_modelo):
        tipo.drop(op.get_bind(), checkfirst=True)
