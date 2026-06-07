"""revert embedding dimension to 384

Revision ID: 20260531_1548_revert_emb_dim
Revises: 7ef45fdad5be
Create Date: 2026-05-31 15:48:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '20260531_1548_revert_emb_dim'
down_revision: Union[str, None] = '7ef45fdad5be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Revert all memory tables' embedding columns back to Vector(384)
    # Cast using postgresql syntax if there is data, or simply alter type if safe.
    # Note: postgres allows type change for pgvector if the dimension changes.
    op.alter_column('episodic_memories', 'embedding', type_=Vector(384), existing_type=Vector(768))
    op.alter_column('semantic_memories', 'embedding', type_=Vector(384), existing_type=Vector(768))
    op.alter_column('procedural_memories', 'embedding', type_=Vector(384), existing_type=Vector(768))


def downgrade() -> None:
    op.alter_column('episodic_memories', 'embedding', type_=Vector(768), existing_type=Vector(384))
    op.alter_column('semantic_memories', 'embedding', type_=Vector(768), existing_type=Vector(384))
    op.alter_column('procedural_memories', 'embedding', type_=Vector(768), existing_type=Vector(384))
