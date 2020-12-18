"""added color_to_move field

Revision ID: e239b1391237
Revises: 965e42327ea2
Create Date: 2020-12-17 09:33:51.709761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e239b1391237'
down_revision = '965e42327ea2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('moves', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color_to_move', sa.String(length=1), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('moves', schema=None) as batch_op:
        batch_op.drop_column('color_to_move')

    # ### end Alembic commands ###