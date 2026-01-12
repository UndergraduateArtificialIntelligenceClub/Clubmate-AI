"""
Alembic Script Template
=======================
Used when generating new migrations.
"""

${imports}

def downgrade() -> None:
    """Reverse the migration."""
    ${downgrades if downgrades else "pass"}


def upgrade() -> None:
    """Apply the migration."""
    ${upgrades if upgrades else "pass"}


# Revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}
