"""20220305_rename_game_questions

Revision ID: 6528c9fc31f8
Revises: 9410ebb42c4b
Create Date: 2022-03-05 11:09:45.897805

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6528c9fc31f8'
down_revision = '9410ebb42c4b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('game_questions', 'game_asked_questions')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('game_asked_questions', 'game_questions')
    # ### end Alembic commands ###