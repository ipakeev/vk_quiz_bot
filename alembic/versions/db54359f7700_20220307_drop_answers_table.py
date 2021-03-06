"""20220307_drop_answers_table

Revision ID: db54359f7700
Revises: 9e0ada5cd216
Create Date: 2022-03-07 22:37:04.720871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db54359f7700'
down_revision = '9e0ada5cd216'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('correct_answers')
    op.add_column('game_user_scores', sa.Column('n_correct_answers', sa.Integer(), nullable=True))
    op.add_column('game_user_scores', sa.Column('n_wrong_answers', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('game_user_scores', 'n_wrong_answers')
    op.drop_column('game_user_scores', 'n_correct_answers')
    op.create_table('correct_answers',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('question_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name='correct_answers_game_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name='correct_answers_question_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='correct_answers_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='correct_answers_pkey')
    )
    # ### end Alembic commands ###
