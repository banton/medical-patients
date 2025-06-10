"""add_version_and_parent_to_config_template

Revision ID: 2b84a220e9ac
Revises: f5e470301516
Create Date: 2025-05-20 11:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2b84a220e9ac"
down_revision: Union[str, None] = "f5e470301516"  # Points to the nationality distribution update
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuration_templates", sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1"))
    )
    op.add_column("configuration_templates", sa.Column("parent_config_id", sa.String(), nullable=True))
    # Add foreign key constraint if parent_config_id refers to configuration_templates.id
    # op.create_foreign_key(
    #     "fk_configuration_templates_parent_config_id", "configuration_templates",
    #     "configuration_templates", ["parent_config_id"], ["id"],
    #     ondelete="SET NULL" # Or "CASCADE" or "RESTRICT" depending on desired behavior
    # )


def downgrade() -> None:
    # op.drop_constraint("fk_configuration_templates_parent_config_id", "configuration_templates", type_="foreignkey")
    op.drop_column("configuration_templates", "parent_config_id")
    op.drop_column("configuration_templates", "version")
