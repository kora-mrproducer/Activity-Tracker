"""Initial migration

Revision ID: ffe97b4a6115
Revises: 
Create Date: 2025-11-08 07:39:33.922195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffe97b4a6115'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('activity_desc', sa.Text(), nullable=False),
        sa.Column('source', sa.String(100)),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date()),
        sa.Column('blocking_points', sa.Text()),
        sa.Column('status', sa.String(50)),
        sa.Column('observations', sa.Text()),
        sa.Column('priority', sa.String(20)),
        sa.Column('tags', sa.Text()))
    for field in ('status', 'priority', 'start_date', 'end_date'):
        op.create_index('idx_' + field, 'activities', [field])
    op.create_table('goals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('text', sa.String(500), nullable=False),
        sa.Column('week_of', sa.Date(), nullable=False),
        sa.Column('is_complete', sa.Boolean()))
    op.create_table('updates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('activity_id', sa.Integer(), sa.ForeignKey('activities.id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('bp_snapshot', sa.Text()))


def downgrade():
    op.drop_table('updates')
    op.drop_table('goals')
    op.drop_table('activities')
