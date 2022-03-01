from app.base.database import db
from app.utils import now


# import typing
# if typing.TYPE_CHECKING:
#     import sqlalchemy as db


# При удалении чата удаляется и игра
class GameModel(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    chat_id = db.Column(db.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    is_stopped = db.Column(db.Boolean(), default=False)
    started_at = db.Column(db.DateTime(), default=now)


# Данные score просто дополняют таблицу "GameUsers", поэтому объединены в эту таблицу
# При удалении игры или пользователя удаляется и score
class GameUserScore(db.Model):
    __tablename__ = "game_user_scores"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer(), default=0)


# При удалении игры или вопроса удаляется и эта запись
class GameQuestion(db.Model):
    __tablename__ = "game_questions"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_answered = db.Column(db.Boolean(), default=False)

    # по истечении времени может не быть правильных ответов,
    # поэтому вводим это поле для определения завершения приема ответов
    is_done = db.Column(db.Boolean(), default=False)

    started_at = db.Column(db.DateTime(), default=now)


# При удалении пользователя, игры или вопроса удаляется и эта запись
class CorrectAnswers(db.Model):
    __tablename__ = "correct_answers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
