"""add postgis geom to cluster array

Revision ID: 9b3c1d7e5a42
Revises: e90a28fc76ee
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9b3c1d7e5a42"
down_revision: Union[str, Sequence[str], None] = "e90a28fc76ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute(
        """
        ALTER TABLE cluster_array
        ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)
        GENERATED ALWAYS AS (
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        ) STORED
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cluster_array_geom
        ON cluster_array
        USING GIST (geom)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_cluster_array_geom")
    op.execute("ALTER TABLE cluster_array DROP COLUMN IF EXISTS geom")
