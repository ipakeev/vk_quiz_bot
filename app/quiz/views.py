import marshmallow
from aiohttp import web_exceptions
from aiohttp_apispec import docs, request_schema, response_schema, querystring_schema

from app.quiz import schemes, models
from app.web.app import View
from app.web.utils import json_response
from app.web.utils import require_login


@require_login
class ThemeAddView(View):

    async def get(self):
        raise web_exceptions.HTTPNotImplemented()

    @docs(description="Add new theme.")
    @request_schema(schemes.AddThemeRequestSchema)
    @response_schema(schemes.AddThemeResponseSchema)
    async def post(self):
        title = self.data['title']

        if await self.store.quiz.get_theme_by_title(title):
            raise web_exceptions.HTTPConflict(text='The theme exists.')

        theme = await self.store.quiz.create_theme(title=title)
        return json_response(
            data=schemes.ThemeSchema().dump(theme),
        )


@require_login
class ThemeListView(View):
    @docs(description="Return list of all themes.")
    @response_schema(schemes.ThemeListResponseSchema)
    async def get(self):
        themes = await self.store.quiz.list_themes()
        themes = models.ListThemesDC(themes=themes)
        return json_response(
            data=schemes.ThemeListSchema().dump(themes),
        )

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()


@require_login
class QuestionAddView(View):

    async def get(self):
        raise web_exceptions.HTTPNotImplemented()

    @docs(description="Add question.")
    @request_schema(schemes.AddQuestionRequestSchema)
    @response_schema(schemes.AddQuestionResponseSchema)
    async def post(self):
        data = self.data
        theme_id = data["theme_id"]
        title = data["title"]
        price = data["price"]
        answers = [models.AnswerDC(**i) for i in data["answers"]]

        if sum([i.is_correct for i in answers]) != 1:
            raise marshmallow.ValidationError(message="Correct answer must be only one.")

        if len(set([i.title for i in answers])) != len(answers):
            raise marshmallow.ValidationError(message="Answers must be unique.")

        if price <= 0:
            raise marshmallow.ValidationError(message="Price must be positive.")

        if not await self.store.quiz.get_theme_by_id(theme_id):
            raise web_exceptions.HTTPNotFound(text=f"Theme with id={theme_id} not found.")

        if await self.store.quiz.get_question_by_title(title):
            raise web_exceptions.HTTPConflict(text=f"Questions with title='{title}' is exists.")

        question = await self.store.quiz.create_question(theme_id, title, price, answers)
        return json_response(
            data=schemes.QuestionSchema().dump(question),
        )


@require_login
class QuestionListView(View):
    @docs(description="List of the questions.")
    @querystring_schema(schemes.QueryThemeIdSchema)
    @response_schema(schemes.ListQuestionResponseSchema)
    async def get(self):
        theme_id = self.request.query.get('theme_id')
        if theme_id is not None:
            theme_id = int(theme_id)
        questions = await self.store.quiz.list_questions(theme_id)
        return json_response(
            data=schemes.ListQuestionSchema().dump(questions),
        )

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()
