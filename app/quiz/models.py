from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from app.base.database import db
from app.utils import now


# import typing
# if typing.TYPE_CHECKING:
#     import sqlalchemy as db


@dataclass
class ThemeDC:
    id: int
    title: str
    created_at: datetime

    def as_dict(self) -> dict:
        return asdict(self)


class ThemeModel(db.Model):
    __tablename__ = "themes"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now)

    def as_dataclass(self) -> ThemeDC:
        return ThemeDC(id=self.id, title=self.title, created_at=self.created_at)


@dataclass
class QuestionDC:
    id: int
    theme_id: int
    title: str
    answers: list["AnswerDC"]

    def as_dict(self) -> dict:
        return asdict(self)


class QuestionModel(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    theme_id = db.Column(db.ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(), nullable=False)

    def __init__(self, *args, **kwargs):
        super(QuestionModel, self).__init__(*args, **kwargs)
        self._answers: list["AnswerModel"] = []

    @property
    def answers(self) -> list["AnswerModel"]:
        return self._answers

    @answers.setter
    def answers(self, answer: "AnswerModel"):
        self._answers.append(answer)

    def as_dataclass(self, answer_models: Optional[list["AnswerModel"]] = None) -> QuestionDC:
        answer_models = answer_models or self.answers
        answer_dcs = [i.as_dataclass() for i in answer_models]
        return QuestionDC(id=self.id, theme_id=self.theme_id, title=self.title, answers=answer_dcs)


@dataclass
class AnswerDC:
    title: str
    is_correct: bool
    description: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


class AnswerModel(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(), nullable=False)
    is_correct = db.Column(db.Boolean(), nullable=False)
    description = db.Column(db.String(), nullable=True)

    def as_dataclass(self) -> AnswerDC:
        return AnswerDC(title=self.title, is_correct=self.is_correct, description=self.description)
