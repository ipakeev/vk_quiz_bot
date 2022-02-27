from typing import Optional

from app.database.accessor import BaseAccessor
from app.quiz.models import (
    ThemeDC, ThemeModel,
    QuestionDC, QuestionModel, QuestionsListDC,
    AnswerDC, AnswerModel,
)


class QuizAccessor(BaseAccessor):

    async def create_theme(self, title: str) -> ThemeDC:
        theme_model: ThemeModel = await ThemeModel.create(title=title)
        return theme_model.as_dataclass()

    async def get_theme_by_title(self, title: str) -> Optional[ThemeDC]:
        theme_model: ThemeModel = await ThemeModel.query.where(ThemeModel.title == title).gino.first()
        if theme_model:
            return theme_model.as_dataclass()

    async def get_theme_by_id(self, id_: int) -> Optional[ThemeDC]:
        theme_model: ThemeModel = await ThemeModel.query.where(ThemeModel.id == id_).gino.first()
        if theme_model:
            return theme_model.as_dataclass()

    async def list_themes(self) -> list[ThemeDC]:
        theme_models: list[ThemeModel] = await ThemeModel.query.gino.all()
        return [i.as_dataclass() for i in theme_models]

    async def create_question(self, theme_id: int, title: str, price: int, answers: list[AnswerDC]) -> QuestionDC:
        question_model: QuestionModel = await QuestionModel.create(theme_id=theme_id, title=title, price=price)
        await self.create_answers(question_model.id, answers)
        return question_model.as_dataclass(answers=answers)

    async def get_question_by_title(self, title: str) -> Optional[QuestionDC]:
        question_model: QuestionModel = await QuestionModel.query.where(QuestionModel.title == title).gino.first()
        if question_model:
            answer_models: list[AnswerModel] = await AnswerModel.query.where(
                AnswerModel.question_id == question_model.id
            ).gino.all()
            return question_model.as_dataclass(answers=[i.as_dataclass() for i in answer_models])

    async def list_questions(self, theme_id: Optional[int] = None) -> QuestionsListDC:
        if theme_id is None:
            question_models: list[QuestionModel] = await QuestionModel.query.gino.all()
        else:
            question_models: list[QuestionModel] = await QuestionModel.query.where(
                QuestionModel.theme_id == theme_id
            ).gino.all()
        questions = []
        for q in question_models:
            answer_models: list[AnswerModel] = await AnswerModel.query.where(
                AnswerModel.question_id == q.id
            ).gino.all()
            questions.append(
                q.as_dataclass(answers=[i.as_dataclass() for i in answer_models])
            )
        return QuestionsListDC(questions=questions)

    async def create_answers(self, question_id, answers: list[AnswerDC]):
        for answer in answers:
            await AnswerModel.create(question_id=question_id,
                                     title=answer.title,
                                     is_correct=answer.is_correct)
