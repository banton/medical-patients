"""Initial empty revision; setup Alembic

Revision ID: 3cf60fdf0504
Revises:
Create Date: 2025-05-16 16:43:18.159527

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3cf60fdf0504"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
