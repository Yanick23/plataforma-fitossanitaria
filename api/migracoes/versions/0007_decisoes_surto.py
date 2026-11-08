"""Decisões do técnico sobre os sinais de surto (confirmar ou descartar).

Revisão: 0007
Anterior: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decisoes_surto",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id"), nullable=False),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("classe", sa.String(60), nullable=False),
        sa.Column("decisao", sa.String(12), nullable=False),
        sa.Column("nota", sa.Text),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_decisoes_surto_distrito_id", "decisoes_surto", ["distrito_id"])
    op.create_index("ix_decisoes_surto_criado_em", "decisoes_surto", ["criado_em"])


def downgrade() -> None:
    op.drop_table("decisoes_surto")
