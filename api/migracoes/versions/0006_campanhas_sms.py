"""Campanhas de vigilância activa e registo dos SMS enviados (alertas e campanhas).

Revisão: 0006
Anterior: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

DATA = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "campanhas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("titulo", sa.String(120), nullable=False),
        sa.Column("mensagem", sa.Text, nullable=False),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("patologia_id", sa.Integer, sa.ForeignKey("patologias.id", ondelete="SET NULL")),
        sa.Column("provincia_codigo", sa.String(10), sa.ForeignKey("provincias.codigo")),
        sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id")),
        sa.Column("inicio", sa.Date, nullable=False),
        sa.Column("fim", sa.Date, nullable=False),
        sa.Column("autor_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("cancelada", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("criado_em", DATA, nullable=False),
    )
    op.create_index("ix_campanhas_provincia_codigo", "campanhas", ["provincia_codigo"])
    op.create_index("ix_campanhas_distrito_id", "campanhas", ["distrito_id"])
    op.create_index("ix_campanhas_criado_em", "campanhas", ["criado_em"])

    op.create_table(
        "envios_sms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alerta_id", sa.Integer, sa.ForeignKey("alertas.id", ondelete="CASCADE")),
        sa.Column("campanha_id", sa.Integer, sa.ForeignKey("campanhas.id", ondelete="CASCADE")),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=False),
        sa.Column("conteudo", sa.Text, nullable=False),
        sa.Column("estado", sa.String(10), nullable=False),
        sa.Column("id_externo", sa.String(80)),
        sa.Column("erro", sa.Text),
        sa.Column("criado_em", DATA, nullable=False),
        sa.Column("actualizado_em", DATA, nullable=False),
    )
    op.create_index("ix_envios_sms_alerta_id", "envios_sms", ["alerta_id"])
    op.create_index("ix_envios_sms_campanha_id", "envios_sms", ["campanha_id"])


def downgrade() -> None:
    op.drop_table("envios_sms")
    op.drop_table("campanhas")
