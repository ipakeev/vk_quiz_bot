from dataclasses import dataclass
from typing import Optional

from app.base.database import db
from app.utils import now


import typing
if typing.TYPE_CHECKING:
    import sqlalchemy as db


@dataclass
class UserDC:
    id: int  # this is vk_id
    first_name: str
    last_name: str

    score: Optional[int] = None
    n_correct_answers: Optional[int] = None


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=now)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._correct_answers = []

    @property
    def correct_answers(self):
        return self._correct_answers

    @correct_answers.setter
    def correct_answers(self, answer):
        self._correct_answers.append(answer)


@dataclass
class ChatDC:
    id: int  # this is vk_id


class ChatModel(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    joined_at = db.Column(db.DateTime(timezone=True), default=now)


# При удалении чата удаляется и игра
class GameModel(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    chat_id = db.Column(db.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    is_stopped = db.Column(db.Boolean(), default=False)
    started_at = db.Column(db.DateTime(timezone=True), default=now)


# Данные score просто дополняют таблицу "GameUsers", поэтому объединены в эту таблицу
# При удалении игры или пользователя удаляется и score
class GameUserScoreModel(db.Model):
    __tablename__ = "game_user_scores"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer(), default=0)


# При удалении игры или вопроса удаляется и эта запись
class GameAskedQuestionModel(db.Model):
    __tablename__ = "game_asked_questions"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    is_answered = db.Column(db.Boolean(), default=False)

    # по истечении времени может не быть правильных ответов,
    # поэтому вводим это поле для определения завершения приема ответов
    is_done = db.Column(db.Boolean(), default=False)

    started_at = db.Column(db.DateTime(timezone=True), default=now)


# При удалении пользователя, игры или вопроса удаляется и эта запись
class CorrectAnswerModel(db.Model):
    __tablename__ = "correct_answers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
