"""Add CHECK constraints for status and priority

Revision ID: a1b2c3d4e5f6
Revises: 3c9fe30224a4
Create Date: 2025-11-08 12:05:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '3c9fe30224a4'
branch_labels = None
depends_on = None

STATUS_ALLOWED = ('Ongoing', 'Closed', 'NA')
PRIORITY_ALLOWED = ('High', 'Medium', 'Low')


def upgrade():
    # Use batch operations to ensure SQLite compatibility (table rebuild under the hood)
    status_expr = f"status IN ({', '.join([repr(v) for v in STATUS_ALLOWED])})"
    priority_expr = f"priority IN ({', '.join([repr(v) for v in PRIORITY_ALLOWED])})"
    with op.batch_alter_table('activities') as batch_op:
        batch_op.create_check_constraint('ck_activities_status', status_expr)
        batch_op.create_check_constraint('ck_activities_priority', priority_expr)


def downgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.drop_constraint('ck_activities_status', type_='check')
        batch_op.drop_constraint('ck_activities_priority', type_='check')
