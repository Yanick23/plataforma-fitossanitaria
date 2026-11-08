"""Áudio em línguas locais: gravações do catálogo e dos alertas, e a língua do utilizador.

Revisão: 0008
Anterior: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("utilizadores") as tabela:
        tabela.add_column(sa.Column("lingua", sa.String(3)))
    op.create_table(
        "audios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patologia_id", sa.Integer, sa.ForeignKey("patologias.id", ondelete="CASCADE")),
        sa.Column("alerta_id", sa.Integer, sa.ForeignKey("alertas.id", ondelete="CASCADE")),
        sa.Column("lingua", sa.String(3), nullable=False),
        sa.Column("caminho_ficheiro", sa.String(300), nullable=False),
        sa.Column("tipo_mime", sa.String(40), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer, nullable=False),
        sa.Column("duracao_s", sa.Float),
        sa.Column("autor_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validado_por_id", sa.Integer, sa.ForeignKey("utilizadores.id")),
        sa.Column("validado_em", sa.DateTime(timezone=True)),
        sa.Column("reproducoes", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_audios_patologia_id", "audios", ["patologia_id"])
    op.create_index("ix_audios_alerta_id", "audios", ["alerta_id"])


def downgrade() -> None:
    op.drop_table("audios")
    with op.batch_alter_table("utilizadores") as tabela:
        tabela.drop_column("lingua")
