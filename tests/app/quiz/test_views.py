from app.quiz.models import QuestionDC, AnswerDC
from tests.utils import ok_response


class TestThemeAddView:
    url = "/quiz.add_theme"

    async def test_success(self, authed_cli):
        title = "title"
        response = await authed_cli.post(
            self.url,
            json=dict(title=title),
        )
        assert response.status == 200

        data = await response.json()
        assert data == ok_response(data=dict(id=1, title=title))

    async def test_fail_on_validation(self, authed_cli):
        response = await authed_cli.post(
            self.url,
        )
        assert response.status == 400

        response = await authed_cli.post(
            self.url,
            json=dict(title=123)
        )
        assert response.status == 400

    async def test_unauthorized(self, cli):
        response = await cli.post(
            self.url,
            json=dict(title="title"),
        )
        assert response.status == 401


class TestThemeListView:
    url = "/quiz.list_themes"

    async def test_success_empty(self, authed_cli):
        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[])

    async def test_success(self, authed_cli, theme):
        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(
            data=[dict(id=theme.id, title=theme.title)],
        )

    async def test_unauthorized(self, cli):
        response = await cli.get(self.url)
        assert response.status == 401


class TestQuestionAddView:
    url = "/quiz.add_question"

    async def test_success(self, authed_cli, theme, answers):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=theme.id,
                      title="title",
                      answers=[i.as_dict() for i in answers]),
        )
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(
            data=QuestionDC(id=1,
                            theme_id=theme.id,
                            title="title",
                            answers=answers).as_dict(),
        )

    async def test_unauthorized(self, cli, question, answers):
        response = await cli.post(
            self.url,
            json=dict(theme_id=1,
                      title="title",
                      answers=[i.as_dict() for i in answers]),
        )
        assert response.status == 401

    async def test_theme_not_found(self, authed_cli, answers):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=1,
                      title="title",
                      answers=[i.as_dict() for i in answers]),
        )
        assert response.status == 404

    async def test_question_exists(self, authed_cli, question, answers):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=question.theme_id,
                      title=question.title,
                      answers=[i.as_dict() for i in answers]),
        )
        assert response.status == 409

    async def test_answers_length(self, authed_cli, theme, answers):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=theme.id,
                      title="title",
                      answers=[i.as_dict() for i in answers][:2]),
        )
        assert response.status == 400

    async def test_answers_are_unique(self, authed_cli, theme):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=theme.id,
                      title="title",
                      answers=[AnswerDC("title1", False).as_dict(),
                               AnswerDC("title1", True, "some description").as_dict(),
                               AnswerDC("title1", False).as_dict(),
                               AnswerDC("title1", False).as_dict()]),
        )
        assert response.status == 400

    async def test_answers_only_one_correct(self, authed_cli, theme):
        response = await authed_cli.post(
            self.url,
            json=dict(theme_id=theme.id,
                      title="title",
                      answers=[AnswerDC("title1", False).as_dict(),
                               AnswerDC("title2", True, "some description").as_dict(),
                               AnswerDC("title3", True, "some description").as_dict(),
                               AnswerDC("title4", False).as_dict()]),
        )
        assert response.status == 400


class TestQuestionListView:
    url = "/quiz.list_questions"

    async def test_unauthorized(self, cli):
        response = await cli.get(self.url)
        assert response.status == 401

    async def test_empty(self, authed_cli):
        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[])

    async def test_questions(self, authed_cli, application, answers):
        theme1 = await application.store.quiz.create_theme("title1")
        theme2 = await application.store.quiz.create_theme("title2")
        question0 = await application.store.quiz.create_question(theme1.id, "title0", answers)
        question1 = await application.store.quiz.create_question(theme1.id, "title1", answers)
        question2 = await application.store.quiz.create_question(theme2.id, "title2", answers)

        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[question0.as_dict(), question1.as_dict(), question2.as_dict()])

        response = await authed_cli.get(self.url, params={"theme_id": 1})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[question0.as_dict(), question1.as_dict()])

        response = await authed_cli.get(self.url, params={"theme_id": 2})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[question2.as_dict()])

        response = await authed_cli.get(self.url, params={"theme_id": 3})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[])


class TestDeleteThemeView:
    url = "/quiz.delete_theme"

    async def test_success(self, authed_cli, theme):
        response = await authed_cli.delete(self.url, params={"theme_id": 1})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=dict(id=theme.id, title=theme.title))

    async def test_unauthorized(self, cli, theme):
        response = await cli.delete(self.url, params={"theme_id": 1})
        assert response.status == 401

    async def test_not_exists(self, authed_cli):
        response = await authed_cli.delete(self.url, params={"theme_id": 1})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data={})

    async def test_no_params(self, authed_cli):
        response = await authed_cli.delete(self.url)
        assert response.status == 400


class TestDeleteQuestionView:
    url = "/quiz.delete_question"

    async def test_success(self, authed_cli, question):
        # don't fetch answers
        question.answers = []

        response = await authed_cli.delete(self.url, params={"question_id": 1})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=question.as_dict())

    async def test_unauthorized(self, cli, question):
        response = await cli.delete(self.url, params={"question_id": 1})
        assert response.status == 401

    async def test_not_exists(self, authed_cli):
        response = await authed_cli.delete(self.url, params={"question_id": 1})
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data={})

    async def test_no_params(self, authed_cli):
        response = await authed_cli.delete(self.url)
        assert response.status == 400
