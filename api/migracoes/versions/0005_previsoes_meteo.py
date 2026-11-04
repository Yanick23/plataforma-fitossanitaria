"""Previsões do tempo guardadas por distrito (risco meteorológico).

Revisão: 0005
Anterior: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "previsoes_meteo",
        sa.Column("distrito_id", sa.Integer, sa.ForeignKey("distritos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("obtida_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dados", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("previsoes_meteo")
