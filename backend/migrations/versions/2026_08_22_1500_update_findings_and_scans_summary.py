"""Update findings table with vulnerability tracking fields and unique fingerprint constraint, add scan_summary to scans

Revision ID: 2026_08_22_1500
Revises: 2026_08_22_1200
Create Date: 2026-08-22 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2026_08_22_1500'
down_revision: Union[str, None] = '2026_08_22_1200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vulnerability tracking columns to findings
    op.add_column('findings', sa.Column('package_name', sa.String(length=255), nullable=True))
    op.add_column('findings', sa.Column('installed_version', sa.String(length=100), nullable=True))
    op.add_column('findings', sa.Column('fixed_version', sa.String(length=100), nullable=True))
    op.add_column('findings', sa.Column('vulnerability_id', sa.String(length=255), nullable=True))
    op.add_column('findings', sa.Column('aliases', sa.JSON(), nullable=True))

    op.create_index(op.f('ix_findings_fingerprint'), 'findings', ['fingerprint'], unique=False)
    op.create_index(op.f('ix_findings_vulnerability_id'), 'findings', ['vulnerability_id'], unique=False)

    # Delete existing duplicate findings prior to adding unique constraint (keeping newest row per repository & fingerprint)
    op.execute("""
        DELETE FROM findings
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY repository_id, fingerprint
                           ORDER BY created_at DESC, id DESC
                       ) as rnum
                FROM findings
            ) t
            WHERE t.rnum > 1
        );
    """)

    # Add unique constraint on (repository_id, fingerprint) to prevent duplicates
    op.create_unique_constraint('uq_repository_fingerprint', 'findings', ['repository_id', 'fingerprint'])

    # Add scan_summary to scans
    op.add_column('scans', sa.Column('scan_summary', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('scans', 'scan_summary')
    op.drop_constraint('uq_repository_fingerprint', 'findings', type_='unique')
    op.drop_index(op.f('ix_findings_vulnerability_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_fingerprint'), table_name='findings')
    op.drop_column('findings', 'aliases')
    op.drop_column('findings', 'vulnerability_id')
    op.drop_column('findings', 'fixed_version')
    op.drop_column('findings', 'installed_version')
    op.drop_column('findings', 'package_name')
