"""Plataforma (fase 1): regiões de Moçambique, zona dos utilizadores, alertas, validação,
pedidos de visita e auditoria.

Revisão: 0002
Anterior: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

nivel_alerta = sa.Enum("INFORMACAO", "AVISO", "URGENTE", name="nivel_alerta")
estado_visita = sa.Enum("PENDENTE", "AGENDADA", "RESOLVIDA", "CANCELADA", name="estado_visita")
DATA = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "provincias",
        sa.Column("codigo", sa.String(10), primary_key=True),
        sa.Column("nome", sa.String(60), nullable=False),
    )
    op.create_table(
        "distritos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(80), nullable=False),
        sa.Column("provincia_codigo", sa.String(10), sa.ForeignKey("provincias.codigo"), nullable=False),
        sa.UniqueConstraint("provincia_codigo", "nome"),
    )
    op.create_index("ix_distritos_provincia_codigo", "distritos", ["provincia_codigo"])

    with op.batch_alter_table("utilizadores") as t:
        t.add_column(sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id", name="fk_utilizadores_distrito")))
        t.add_column(sa.Column("provincia_codigo", sa.String(10),
                               sa.ForeignKey("provincias.codigo", name="fk_utilizadores_provincia")))
        t.add_column(sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()))
        t.create_index("ix_utilizadores_distrito_id", ["distrito_id"])
        t.create_index("ix_utilizadores_provincia_codigo", ["provincia_codigo"])
    with op.batch_alter_table("diagnosticos") as t:
        t.add_column(sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id", name="fk_diagnosticos_distrito")))
        t.create_index("ix_diagnosticos_distrito_id", ["distrito_id"])

    op.create_table(
        "alertas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("titulo", sa.String(120), nullable=False),
        sa.Column("mensagem", sa.Text, nullable=False),
        sa.Column("nivel", nivel_alerta, nullable=False),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id")),
        sa.Column("patologia_id", sa.Integer, sa.ForeignKey("patologias.id", ondelete="SET NULL")),
        sa.Column("provincia_codigo", sa.String(10), sa.ForeignKey("provincias.codigo")),
        sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id")),
        sa.Column("autor_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("criado_em", DATA, nullable=False),
        sa.Column("expira_em", DATA),
        sa.Column("arquivado", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_alertas_provincia_codigo", "alertas", ["provincia_codigo"])
    op.create_index("ix_alertas_distrito_id", "alertas", ["distrito_id"])
    op.create_index("ix_alertas_criado_em", "alertas", ["criado_em"])
    op.create_table(
        "alertas_leituras",
        sa.Column("alerta_id", sa.Integer, sa.ForeignKey("alertas.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id"), primary_key=True),
        sa.Column("lido_em", DATA, nullable=False),
    )

    op.create_table(
        "validacoes",
        sa.Column("diagnostico_id", sa.String(36), sa.ForeignKey("diagnosticos.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("tecnico_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("classe_confirmada", sa.String(60), nullable=False),
        sa.Column("correcto", sa.Boolean, nullable=False),
        sa.Column("nota", sa.Text),
        sa.Column("criado_em", DATA, nullable=False),
        sa.Column("actualizado_em", DATA, nullable=False),
    )
    op.create_table(
        "pedidos_visita",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("diagnostico_id", sa.String(36), sa.ForeignKey("diagnosticos.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("agricultor_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("tecnico_id", sa.Integer, sa.ForeignKey("utilizadores.id")),
        sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id")),
        sa.Column("estado", estado_visita, nullable=False),
        sa.Column("mensagem", sa.Text),
        sa.Column("data_agendada", DATA),
        sa.Column("notas_tecnico", sa.Text),
        sa.Column("criado_em", DATA, nullable=False),
        sa.Column("actualizado_em", DATA, nullable=False),
    )
    for coluna in ("diagnostico_id", "agricultor_id", "distrito_id", "criado_em"):
        op.create_index(f"ix_pedidos_visita_{coluna}", "pedidos_visita", [coluna])

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id")),
        sa.Column("accao", sa.String(60), nullable=False),
        sa.Column("entidade", sa.String(40), nullable=False),
        sa.Column("entidade_id", sa.String(60)),
        sa.Column("detalhes", sa.Text),
        sa.Column("criado_em", DATA, nullable=False),
    )
    for coluna in ("utilizador_id", "accao", "criado_em"):
        op.create_index(f"ix_auditoria_{coluna}", "auditoria", [coluna])


def downgrade() -> None:
    for tabela in ("auditoria", "pedidos_visita", "validacoes", "alertas_leituras", "alertas"):
        op.drop_table(tabela)
    with op.batch_alter_table("diagnosticos") as t:
        t.drop_index("ix_diagnosticos_distrito_id")
        t.drop_constraint("fk_diagnosticos_distrito", type_="foreignkey")
        t.drop_column("distrito_id")
    with op.batch_alter_table("utilizadores") as t:
        t.drop_index("ix_utilizadores_provincia_codigo")
        t.drop_index("ix_utilizadores_distrito_id")
        t.drop_constraint("fk_utilizadores_provincia", type_="foreignkey")
        t.drop_constraint("fk_utilizadores_distrito", type_="foreignkey")
        for coluna in ("activo", "provincia_codigo", "distrito_id"):
            t.drop_column(coluna)
    op.drop_table("distritos")
    op.drop_table("provincias")
    estado_visita.drop(op.get_bind(), checkfirst=True)
    nivel_alerta.drop(op.get_bind(), checkfirst=True)
