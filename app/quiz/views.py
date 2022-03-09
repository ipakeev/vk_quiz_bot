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
        data = self.data
        self.request.app.logger.debug(f"post ThemeAddView: {data}")

        theme = await self.store.quiz.create_theme(title=data["title"])
        return json_response(
            data=schemes.ThemeSchema().dump(theme),
        )


@require_login
class ThemeListView(View):
    @docs(description="Return list of all themes.")
    @response_schema(schemes.ThemeListResponseSchema)
    async def get(self):
        self.request.app.logger.debug("get ThemeListview")
        list_themes = await self.store.quiz.list_themes()
        return json_response(
            data=schemes.ThemeListSchema().dump(list_themes),
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
        self.request.app.logger.debug(f"post QuestionAddView: {data}")

        theme_id = data["theme_id"]
        title = data["title"]
        answers = [models.AnswerDC(**i) for i in data["answers"]]

        if sum([i.is_correct for i in answers]) != 1:
            raise marshmallow.ValidationError(message="Correct answer must be only one.")

        if len(set([i.title for i in answers])) != len(answers):
            raise marshmallow.ValidationError(message="Answers must be unique.")

        if not await self.store.quiz.get_theme_by_id(theme_id):
            raise web_exceptions.HTTPNotFound(text=f"Theme with id={theme_id} not found.")

        if await self.store.quiz.get_question_by_title(title):
            raise web_exceptions.HTTPConflict(text=f"Questions with title='{title}' is exists.")

        question = await self.store.quiz.create_question(theme_id, title, answers)
        return json_response(
            data=schemes.QuestionSchema().dump(question),
        )


@require_login
class QuestionListView(View):
    @docs(description="List of the questions.")
    @querystring_schema(schemes.QueryThemeIdSchema)
    @response_schema(schemes.ListQuestionResponseSchema)
    async def get(self):
        self.request.app.logger.debug("get QuestionListView")
        theme_id = schemes.QueryThemeIdSchema().load(self.request.query).get("theme_id")
        questions = await self.store.quiz.list_questions(theme_id)
        return json_response(
            data=schemes.ListQuestionSchema().dump(questions),
        )

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()


@require_login
class DeleteThemeView(View):

    async def get(self):
        raise web_exceptions.HTTPNotImplemented()

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()

    @docs(description="Delete theme by id.")
    @request_schema(schemes.DeleteThemeRequestSchema)
    @response_schema(schemes.DeleteThemeResponseSchema)
    async def delete(self):
        data = self.data
        self.request.app.logger.debug(f"delete theme {data}")
        theme = await self.store.quiz.delete_theme(data["theme_id"])
        return json_response(
            data=schemes.ThemeSchema().dump(theme),
        )


@require_login
class DeleteQuestionView(View):

    async def get(self):
        raise web_exceptions.HTTPNotImplemented()

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()

    @docs(description="Delete question by id.")
    @request_schema(schemes.DeleteQuestionRequestSchema)
    @response_schema(schemes.DeleteQuestionResponseSchema)
    async def delete(self):
        data = self.data
        self.request.app.logger.debug(f"delete question {data}")
        question = await self.store.quiz.delete_question(data["question_id"])
        return json_response(
            data=schemes.QuestionSchema().dump(question),
        )
