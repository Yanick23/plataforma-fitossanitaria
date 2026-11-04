"""Perfis finos (coordenador provincial e investigador) e notificações da equipa (declaração obrigatória).

Revisão: 0004
Anterior: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

DATA = sa.DateTime(timezone=True)


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        # Em PostgreSQL o perfil é um tipo ENUM: acrescentam-se os valores novos.
        # (No SQLite é texto e não precisa de alteração.)
        for valor in ("COORDENADOR", "INVESTIGADOR"):
            op.execute(f"ALTER TYPE perfil ADD VALUE IF NOT EXISTS '{valor}'")

    op.create_table(
        "notificacoes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(160), nullable=False),
        sa.Column("mensagem", sa.Text, nullable=False),
        sa.Column("diagnostico_id", sa.String(36), sa.ForeignKey("diagnosticos.id", ondelete="CASCADE")),
        sa.Column("criado_em", DATA, nullable=False),
        sa.Column("lida_em", DATA),
    )
    op.create_index("ix_notificacoes_utilizador_id", "notificacoes", ["utilizador_id"])
    op.create_index("ix_notificacoes_criado_em", "notificacoes", ["criado_em"])


def downgrade() -> None:
    op.drop_table("notificacoes")
    # Os valores de um ENUM do PostgreSQL não se removem; as contas com estes perfis
    # devem ser passadas a TECNICO antes de descer abaixo da revisão 0004.
