from typing import Optional

from sqlalchemy.dialects.postgresql import insert

from app.base.accessor import BaseAccessor
from app.quiz.models import (
    ThemeDC, ThemeModel, ThemesListDC,
    QuestionDC, QuestionModel, QuestionsListDC,
    AnswerDC, AnswerModel,
)


class QuizAccessor(BaseAccessor):

    async def create_theme(self, title: str) -> ThemeDC:
        # за один поход в базу добавляем тему (либо обновляем, если данная тема уже есть)
        # on_conflict_do_nothing не возвращает ничего, поэтому используем on_conflict_do_update
        stmt = insert(ThemeModel).values(title=title)
        query = stmt.on_conflict_do_update(
            index_elements=[ThemeModel.title], set_=dict(title=stmt.excluded.title)
        ).returning(*ThemeModel)
        theme_model: ThemeModel = await query.gino.model(ThemeModel).first()
        return theme_model.as_dataclass()

    async def get_theme_by_title(self, title: str) -> Optional[ThemeDC]:
        theme_model: ThemeModel = await ThemeModel.query.where(ThemeModel.title == title).gino.first()
        if theme_model:
            return theme_model.as_dataclass()

    async def get_theme_by_id(self, id_: int) -> Optional[ThemeDC]:
        theme_model: ThemeModel = await ThemeModel.query.where(ThemeModel.id == id_).gino.first()
        if theme_model:
            return theme_model.as_dataclass()

    async def list_themes(self) -> ThemesListDC:
        theme_models: list[ThemeModel] = await ThemeModel.query.gino.all()
        # используется ThemesListDC, так как при list[ThemeDC] marshmallow.dump() не выдает результат
        return ThemesListDC(themes=[i.as_dataclass() for i in theme_models])

    async def create_question(self, theme_id: int, title: str, price: int, answers: list[AnswerDC]) -> QuestionDC:
        # валидация того, что данный вопрос с ответами уже есть в базе, происходит на уровне view
        question_model: QuestionModel = await QuestionModel.create(theme_id=theme_id, title=title, price=price)
        answer_models = await self.create_answers(question_model.id, answers)
        return question_model.as_dataclass(answer_models=answer_models)

    async def get_question_by_title(self, title: str) -> Optional[QuestionDC]:
        question_model: QuestionModel = await QuestionModel.query.where(QuestionModel.title == title).gino.first()
        if question_model:
            answer_models: list[AnswerModel] = await AnswerModel.query.where(
                AnswerModel.question_id == question_model.id
            ).gino.all()
            return question_model.as_dataclass(answer_models=answer_models)

    async def list_questions(self, theme_id: Optional[int] = None) -> QuestionsListDC:
        query = QuestionModel.join(AnswerModel, QuestionModel.id == AnswerModel.question_id).select()
        if theme_id is not None:
            query = query.where(QuestionModel.theme_id == theme_id)
        questions: list[QuestionModel] = await query.gino.load(
            QuestionModel.distinct(QuestionModel.id).load(
                answers=AnswerModel.load()
            )
        ).all()
        return QuestionsListDC(questions=[i.as_dataclass() for i in questions])

    async def create_answers(self, question_id, answers: list[AnswerDC]) -> list[AnswerModel]:
        # за один поход в базу добавляем все ответы
        # валидация того, что данный вопрос с ответами уже есть в базе, происходит на уровне view
        # on_conflict_do_update требует уникальный ключ. Значит, необходимо изменить первичный ключ модели?
        await AnswerModel.insert().gino.all([dict(question_id=question_id, **i.as_dict()) for i in answers])
        answer_models = await AnswerModel.query.where(AnswerModel.question_id == question_id).gino.all()
        return answer_models
