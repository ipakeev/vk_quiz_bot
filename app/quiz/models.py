from dataclasses import dataclass
from datetime import datetime

from app.database.database import db
from app.utils import now


# import typing
# if typing.TYPE_CHECKING:
#     import sqlalchemy as db


@dataclass
class ThemeDC:
    id: int
    title: str
    created_at: datetime


@dataclass
class ListThemesDC:
    themes: list[ThemeDC]


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
    price: int
    answers: list["AnswerDC"]


@dataclass
class QuestionsListDC:
    questions: list[QuestionDC]


class QuestionModel(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    theme_id = db.Column(db.ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(), nullable=False)
    price = db.Column(db.Integer(), nullable=False)

    def as_dataclass(self, answers: list["AnswerDC"]) -> QuestionDC:
        return QuestionDC(id=self.id, theme_id=self.theme_id, title=self.title, price=self.price, answers=answers)


@dataclass
class AnswerDC:
    title: str
    is_correct: bool


class AnswerModel(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    question_id = db.Column(db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(), nullable=False)
    is_correct = db.Column(db.Boolean(), nullable=False)

    def as_dataclass(self) -> AnswerDC:
        return AnswerDC(title=self.title, is_correct=self.is_correct)
