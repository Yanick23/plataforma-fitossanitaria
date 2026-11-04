"""Esquema inicial (versão testada no PFC): utilizadores, catálogo, modelos e diagnósticos.

Revisão: 0001
Anterior: nenhuma
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

perfil = sa.Enum("AGRICULTOR", "TECNICO", "ADMINISTRADOR", name="perfil")
tipo_patologia = sa.Enum("DOENCA", "PRAGA", "SAUDAVEL", name="tipo_patologia")


def upgrade() -> None:
    op.create_table(
        "utilizadores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=False),
        sa.Column("hash_palavra_passe", sa.String(100), nullable=False),
        sa.Column("perfil", perfil, nullable=False),
        sa.Column("area", sa.String(80)),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_utilizadores_telefone", "utilizadores", ["telefone"], unique=True)
    op.create_index("ix_utilizadores_area", "utilizadores", ["area"])

    op.create_table(
        "culturas",
        sa.Column("id", sa.String(30), primary_key=True),
        sa.Column("nome", sa.String(60), nullable=False),
        sa.Column("nome_cientifico", sa.String(120), nullable=False),
    )
    op.create_table(
        "patologias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("codigo", sa.String(60), nullable=False),
        sa.Column("nome_local", sa.String(120), nullable=False),
        sa.Column("nome_cientifico", sa.String(200), nullable=False),
        sa.Column("tipo", tipo_patologia, nullable=False),
        sa.Column("recomendacao", sa.Text, nullable=False),
        sa.UniqueConstraint("cultura_id", "codigo"),
    )
    op.create_table(
        "modelos_ml",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("versao", sa.Integer, nullable=False),
        sa.Column("caminho_tflite", sa.String(300), nullable=False),
        sa.Column("classes", sa.Text, nullable=False),
        sa.Column("acuracia_teste", sa.Float),
        sa.Column("tamanho_bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("cultura_id", "versao"),
    )
    op.create_table(
        "diagnosticos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("utilizador_id", sa.Integer, sa.ForeignKey("utilizadores.id"), nullable=False),
        sa.Column("cultura_id", sa.String(30), sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("classe_prevista", sa.String(60), nullable=False),
        sa.Column("confianca", sa.Float, nullable=False),
        sa.Column("data", sa.DateTime(timezone=True), nullable=False),
        sa.Column("versao_modelo", sa.Integer),
        sa.Column("tempo_inferencia_ms", sa.Integer),
        sa.Column("recebido_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diagnosticos_utilizador_id", "diagnosticos", ["utilizador_id"])
    op.create_table(
        "imagens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("diagnostico_id", sa.String(36), sa.ForeignKey("diagnosticos.id"), nullable=False, unique=True),
        sa.Column("caminho_ficheiro", sa.String(300), nullable=False),
        sa.Column("data_captura", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for tabela in ("imagens", "diagnosticos", "modelos_ml", "patologias", "culturas", "utilizadores"):
        op.drop_table(tabela)
    tipo_patologia.drop(op.get_bind(), checkfirst=True)
    perfil.drop(op.get_bind(), checkfirst=True)
