import pytest

from app.game.models import ChatDC, GameDC
from app.quiz.models import AnswerDC, ThemeDC, QuestionDC
from app.store.vk_api.responses import VKUser
from app.web.app import Application


@pytest.fixture
def answers() -> list[AnswerDC]:
    return [AnswerDC("title1", False),
            AnswerDC("title2", True, "some description"),
            AnswerDC("title3", False),
            AnswerDC("title4", False)]


@pytest.fixture
def theme(application, loop) -> ThemeDC:
    return loop.run_until_complete(
        application.store.quiz.create_theme("title")
    )


@pytest.fixture
def question(application, loop, theme, answers) -> QuestionDC:
    return loop.run_until_complete(
        application.store.quiz.create_question(theme.id, "title", answers)
    )


@pytest.fixture
def chat_id() -> int:
    return 12345


@pytest.fixture
def user1() -> VKUser:
    return VKUser(dict(id=1, first_name="Ivan", last_name="Ivanov"))


@pytest.fixture
def user2() -> VKUser:
    return VKUser(dict(id=2, first_name="Peter", last_name="Petrov"))


async def setup_chat(application: Application, chat_id: int) -> ChatDC:
    await application.store.games.joined_the_chat(chat_id)
    chats = await application.store.games.get_chats()
    return chats[0]


async def setup_game(application: Application, chat_id: int, user1: VKUser, user2: VKUser) -> GameDC:
    theme = await application.store.quiz.create_theme("title")
    for title in ["title1", "title2", "title3"]:
        await application.store.quiz.create_question(
            theme.id,
            title,
            answers=[AnswerDC("title1", False),
                     AnswerDC("title2", True, "some description"),
                     AnswerDC("title3", False),
                     AnswerDC("title4", False)])

    await application.store.games.joined_the_chat(chat_id)
    users = await application.store.games.create_users([user1, user2])
    game_dc = await application.store.games.create_game(chat_id, users)
    return game_dc


@pytest.fixture
def chat(loop, application, chat_id) -> ChatDC:
    return loop.run_until_complete(setup_chat(application, chat_id))


@pytest.fixture
def game(loop, application, chat_id, user1, user2) -> GameDC:
    return loop.run_until_complete(setup_game(application, chat_id, user1, user2))
