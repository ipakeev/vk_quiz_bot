import typing
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from app.base.database import db
from app.utils import now

if typing.TYPE_CHECKING:
    import sqlalchemy as db


@dataclass
class UserDC:
    id: int  # this is vk_id
    first_name: str
    last_name: str
    joined_at: Optional[datetime] = None
    score: Optional[int] = None
    n_correct_answers: Optional[int] = None
    n_wrong_answers: Optional[int] = None


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=now)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.score = 0
        self.n_correct_answers = 0
        self.n_wrong_answers = 0

    def as_dataclass(self) -> UserDC:
        return UserDC(id=self.id,
                      first_name=self.first_name,
                      last_name=self.last_name,
                      joined_at=self.joined_at,
                      score=self.score,
                      n_correct_answers=self.n_correct_answers,
                      n_wrong_answers=self.n_wrong_answers)


@dataclass
class ChatDC:
    id: int  # this is vk_id
    joined_at: Optional[datetime] = None


class ChatModel(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    joined_at = db.Column(db.DateTime(timezone=True), default=now)

    def as_dataclass(self) -> ChatDC:
        return ChatDC(id=self.id, joined_at=self.joined_at)


@dataclass
class GameDC:
    id: int
    chat_id: int
    is_stopped: bool
    started_at: datetime
    finished_at: Optional[datetime]
    users: list[UserDC]


# При удалении чата удаляется и игра
class GameModel(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    chat_id = db.Column(db.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    is_stopped = db.Column(db.Boolean(), default=False)
    started_at = db.Column(db.DateTime(timezone=True), default=now)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __init__(self, *args, **kwargs):
        super(GameModel, self).__init__(*args, **kwargs)
        self._users: list[UserModel] = []
        self._scores: list[GameUserScoreModel] = []

    @property
    def scores(self):
        return self._scores

    @scores.setter
    def scores(self, value):
        self._scores.append(value)

    @property
    def users(self):
        return self._users

    @users.setter
    def users(self, value):
        self._users.append(value)

    def as_dataclass(self) -> GameDC:
        scores: dict[int, GameUserScoreModel] = {i.user_id: i for i in self.scores}
        for user in self._users:
            user.score = scores[user.id].score
            user.n_correct_answers = scores[user.id].n_correct_answers
            user.n_wrong_answers = scores[user.id].n_wrong_answers
        self._users.sort(key=lambda i: i.score, reverse=True)
        return GameDC(id=self.id,
                      chat_id=self.chat_id,
                      is_stopped=self.is_stopped,
                      started_at=self.started_at,
                      finished_at=self.finished_at,
                      users=[i.as_dataclass() for i in self._users])


# Данные score просто дополняют таблицу "GameUsers", поэтому объединены в эту таблицу
# При удалении игры или пользователя удаляется и score
class GameUserScoreModel(db.Model):
    __tablename__ = "game_user_scores"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    game_id = db.Column(db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer(), default=0)
    n_correct_answers = db.Column(db.Integer(), default=0)
    n_wrong_answers = db.Column(db.Integer(), default=0)


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


@dataclass
class TopWinnerDC:
    id: int
    first_name: str
    last_name: str
    joined_at: datetime
    win_count: int


@dataclass
class TopScorerDC:
    id: int
    first_name: str
    last_name: str
    joined_at: datetime
    score: int


@dataclass
class GameStatsDC:
    games_total: int
    games_average_per_day: float
    duration_total: int
    duration_average: float
    top_winners: list[TopWinnerDC]
    top_scorers: list[TopScorerDC]

    def as_dict(self) -> dict:
        return asdict(self)
