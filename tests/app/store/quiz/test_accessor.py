from app.quiz.models import AnswerDC
from app.utils import now
from tests.utils import check_empty_table_exists


class TestQuizAccessor:

    async def test_tables_exists(self, application):
        await check_empty_table_exists(application, "themes")
        await check_empty_table_exists(application, "questions")
        await check_empty_table_exists(application, "answers")

    async def test_create_theme(self, application):
        title = "title"
        tt = now()
        theme = await application.store.quiz.create_theme(title)
        assert theme.id == 1
        assert theme.title == title
        assert tt <= theme.created_at <= now()

        assert (await application.store.quiz.create_theme(title)) == theme

    async def test_get_theme_by_title(self, application, theme):
        assert (await application.store.quiz.get_theme_by_title(theme.title)) == theme
        assert (await application.store.quiz.get_theme_by_title("not_existed_title")) is None

    async def test_get_theme_by_id(self, application, theme):
        assert (await application.store.quiz.get_theme_by_id(theme.id)) == theme
        assert (await application.store.quiz.get_theme_by_id(123)) is None

    async def test_list_themes(self, application):
        assert (await application.store.quiz.list_themes()) == []

        theme1 = await application.store.quiz.create_theme("title1")
        theme2 = await application.store.quiz.create_theme("title2")
        themes = await application.store.quiz.list_themes()
        assert themes == [theme1, theme2]

    async def test_create_question(self, application, theme, answers):
        question = await application.store.quiz.create_question(theme.id, "title", answers)
        assert question.id == 1
        assert question.theme_id == theme.id
        assert question.title == "title"
        assert question.answers == answers

    async def test_get_question_by_title(self, application, question):
        assert (await application.store.quiz.get_question_by_title(question.title)) == question
        assert (await application.store.quiz.get_question_by_title("not_existed_title")) is None

    async def test_empty_list_questions(self, application, theme):
        assert (await application.store.quiz.list_questions()) == []
        assert (await application.store.quiz.list_questions(theme.id)) == []

    async def test_list_questions(self, application, theme, answers):
        theme2 = await application.store.quiz.create_theme("title2")
        other_answers = [AnswerDC("2title1", False),
                         AnswerDC("2title2", False),
                         AnswerDC("2title3", True, "some description"),
                         AnswerDC("2title4", False)]

        question0 = await application.store.quiz.create_question(theme.id, "title0", answers)
        question1 = await application.store.quiz.create_question(theme.id, "title1", other_answers)
        question2 = await application.store.quiz.create_question(theme2.id, "title2", other_answers)

        qs = await application.store.quiz.list_questions()
        assert qs == [question0, question1, question2]
        assert qs[0].answers == answers
        assert qs[1].answers == other_answers
        assert qs[2].answers == other_answers

        qs = await application.store.quiz.list_questions(theme.id)
        assert qs == [question0, question1]
        assert qs[0].answers == answers
        assert qs[1].answers == other_answers

        qs = await application.store.quiz.list_questions(theme2.id)
        assert qs == [question2]
        assert qs[0].answers == other_answers

    async def test_get_answers(self, application, question, answers):
        assert (await application.store.quiz.get_answers(question.id)) == answers
        assert (await application.store.quiz.get_answers(123)) == []

    async def test_delete_theme(self, application, theme):
        assert (await application.store.quiz.delete_theme(theme.id)) == theme
        assert (await application.store.quiz.get_theme_by_id(theme.id)) is None

        assert (await application.store.quiz.delete_theme(123)) is None

    async def test_delete_question(self, application, question):
        # don't fetch answers
        question.answers = []
        assert (await application.store.quiz.delete_question(question.id)) == question
        assert (await application.store.quiz.get_question_by_title(question.title)) is None
        assert (await application.store.quiz.get_answers(question.id)) == []

        assert (await application.store.quiz.delete_question(123)) is None

    async def test_cascade_delete_theme(self, application, theme, question):
        await application.store.quiz.delete_theme(theme.id)
        assert (await application.store.quiz.get_theme_by_id(theme.id)) is None
        assert (await application.store.quiz.get_question_by_title(question.title)) is None
        assert (await application.store.quiz.get_answers(question.id)) == []
