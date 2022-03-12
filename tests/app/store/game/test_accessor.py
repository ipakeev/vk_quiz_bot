import asyncio
from datetime import datetime, timezone, timedelta

import pytest
from freezegun import freeze_time

from app.game.models import UserDC
from app.quiz.models import AnswerDC
from app.store.game.payload import BotActions
from app.utils import now


class TestStateAccessor:

    async def test_lock(self, application, chat_id):
        times = []
        application.store.states.set_game_status(chat_id, BotActions.start_game)

        async def task():
            async with application.store.states.locks.game_status(chat_id):
                assert application.store.states.get_game_status(chat_id) == BotActions.start_game
                await asyncio.sleep(1.0)
                assert application.store.states.get_game_status(chat_id) == BotActions.start_game
                application.store.states.set_game_status(chat_id, BotActions.main_menu)
                times.append(now())
                await asyncio.sleep(1.0)

        asyncio.create_task(task())
        await asyncio.sleep(0.1)

        async with application.store.states.locks.game_status(chat_id):
            times.append(now())
            assert application.store.states.get_game_status(chat_id) == BotActions.main_menu
            application.store.states.set_game_status(chat_id, BotActions.show_scoreboard)

        assert application.store.states.get_game_status(chat_id) == BotActions.show_scoreboard
        assert times[0] < times[1]

    async def test_restore_status(self, application, chat_id):
        application.store.states.restore_status(chat_id)

        assert application.store.states.get_game_status(chat_id) == BotActions.main_menu
        assert application.store.states.get_game_id(chat_id) is None
        assert application.store.states.get_joined_users(chat_id) == []
        assert application.store.states.get_theme_chosen_prices(chat_id) == {}
        with pytest.raises(AttributeError):
            application.store.states.get_who_s_turn(chat_id)
        with pytest.raises(AttributeError):
            application.store.states.get_current_question_id(chat_id)
        with pytest.raises(AttributeError):
            application.store.states.get_current_price(chat_id)
        with pytest.raises(AttributeError):
            application.store.states.get_current_answer(chat_id)
        assert application.store.states.get_answered_users(chat_id) == []

    async def test_question_ended(self, application, chat_id):
        application.store.states.question_ended(chat_id)
        with pytest.raises(AttributeError):
            application.store.states.get_current_price(chat_id)
        with pytest.raises(AttributeError):
            application.store.states.get_current_answer(chat_id)
        assert application.store.states.get_answered_users(chat_id) == []

    async def test_game_id(self, application, chat_id):
        assert application.store.states.get_game_id(chat_id) is None
        application.store.states.set_game_id(chat_id, 123)
        assert application.store.states.get_game_id(chat_id) == 123

        application.store.states.restore_status(chat_id)
        assert application.store.states.get_game_id(chat_id) is None

    async def test_game_status(self, application, chat_id):
        assert application.store.states.get_game_status(chat_id) == BotActions.main_menu
        application.store.states.set_game_status(chat_id, "status")
        assert application.store.states.get_game_status(chat_id) == "status"

        application.store.states.restore_status(chat_id)
        assert application.store.states.get_game_status(chat_id) == BotActions.main_menu

        assert application.store.states.get_game_status(chat_id + 1) is None

    async def test_joined_users(self, application, chat_id, user1, user2):
        assert application.store.states.get_joined_users(chat_id) == []
        application.store.states.set_users_joined(chat_id, [user1, user2])
        assert application.store.states.get_joined_users(chat_id) == [user1, user2]

        application.store.states.restore_status(chat_id)
        assert application.store.states.get_joined_users(chat_id) == []

    async def test_user_info(self, application, chat_id, user1):
        application.store.states.set_user_info(user1)
        assert application.store.states.get_user_info(user1.id) == user1

    async def test_who_s_turn(self, application, chat_id, user1):
        application.store.states.set_who_s_turn(chat_id, user1.id)
        assert application.store.states.get_who_s_turn(chat_id) == user1.id

    async def test_theme_chosen_prices(self, application, chat_id):
        chosen_prices = {1: [1, 2, 5]}
        application.store.states.set_theme_chosen_prices(chat_id, chosen_prices)
        assert application.store.states.get_theme_chosen_prices(chat_id) == chosen_prices

    async def test_current_question_id(self, application, chat_id):
        application.store.states.set_current_question_id(chat_id, 3)
        assert application.store.states.get_current_question_id(chat_id) == 3

    async def test_current_price(self, application, chat_id):
        application.store.states.set_current_price(chat_id, 500)
        assert application.store.states.get_current_price(chat_id) == 500

    async def test_current_answer(self, application, chat_id):
        answer = AnswerDC(title="title", is_correct=True, description="desc")
        application.store.states.set_current_answer(chat_id, answer)
        assert application.store.states.get_current_answer(chat_id) == answer

    async def test_answered_users(self, application, chat_id):
        application.store.states.set_users_answered(chat_id, [1, 2, 3])
        assert application.store.states.get_answered_users(chat_id) == [1, 2, 3]

    async def test_previous_text(self, application, chat_id):
        application.store.states.set_previous_text(chat_id, "text")
        assert application.store.states.get_previous_text(chat_id) == "text"

    async def test_flood_detected(self, application, chat_id):
        assert application.store.states.is_flood_detected(chat_id) is False
        application.store.states.set_flood_detected(chat_id)
        assert application.store.states.is_flood_detected(chat_id) is True
        application.store.states.set_flood_not_detected(chat_id)
        assert application.store.states.is_flood_detected(chat_id) is False

    async def test_flood_not_detected_after_hour(self, application, chat_id):
        with freeze_time(datetime.now(tz=timezone.utc) - timedelta(minutes=10)):
            application.store.states.set_flood_detected(chat_id)
            assert application.store.states.is_flood_detected(chat_id) is True
        assert application.store.states.is_flood_detected(chat_id) is False


class TestGameAccessor:

    async def test_restore_status(self, application, game):
        tt = now()
        await application.store.games.restore_status(game.chat_id)
        game_dc = await application.store.games.get_game_by_id(game.id)
        assert game_dc.is_stopped
        assert tt <= game_dc.finished_at <= now()

    async def test_joined_the_chat(self, application, chat_id):
        assert (await application.store.games.get_chats()) == []
        await application.store.games.joined_the_chat(chat_id)
        chats = await application.store.games.get_chats()
        assert [i.id for i in chats] == [chat_id]
        await application.store.games.joined_the_chat(chat_id)
        chats = await application.store.games.get_chats()
        assert [i.id for i in chats] == [chat_id]

        await application.store.games.joined_the_chat(chat_id + 1)
        chats = await application.store.games.get_chats()
        assert [i.id for i in chats] == [chat_id, chat_id + 1]

    async def test_create_users(self, application, user1, user2):
        assert (await application.store.games.create_users([])) == []

        users = [user1]
        user_dcs = await application.store.games.create_users(users)
        assert len(user_dcs) == len(users)
        for dc, vk in zip(user_dcs, users):
            assert isinstance(dc, UserDC)
            assert dc.id == vk.id
            assert dc.first_name == vk.first_name
            assert dc.last_name == vk.last_name

        users = [user1, user2]
        user_dcs = await application.store.games.create_users(users)
        assert len(user_dcs) == len(users)
        for dc, vk in zip(user_dcs, users):
            assert isinstance(dc, UserDC)
            assert dc.id == vk.id
            assert dc.first_name == vk.first_name
            assert dc.last_name == vk.last_name

    async def test_create_game(self, application, chat, user1, user2):
        tt = now()
        users = await application.store.games.create_users([user1, user2])
        game = await application.store.games.create_game(chat.id, users)
        assert game.id == 1
        assert game.chat_id == chat.id
        assert game.is_stopped is False
        assert tt <= game.started_at <= now()
        assert game.finished_at is None

    async def test_get_game_by_id(self, application, game):
        same_game = await application.store.games.get_game_by_id(game.id)
        assert same_game == game
        assert (await application.store.games.get_game_by_id(game.id + 1)) is None

    async def test_get_game_scores(self, application, game, user1, user2):
        users = await application.store.games.get_game_scores(game.id)
        assert len(users) == 2
        assert users[0].id == user1.id
        assert users[1].id == user2.id
        for u in users:
            assert u.score == 0
            assert u.n_correct_answers == 0
            assert u.n_wrong_answers == 0

    async def test_update_game_scores(self, application, game, user1, user2):
        await application.store.games.update_game_scores(game.id, None, [], 1000)
        await self.test_get_game_scores(application, game, user1, user2)  # zero values as well

        await application.store.games.update_game_scores(game.id, user2.id, [], 1000)
        users = await application.store.games.get_game_scores(game.id)
        assert len(users) == 2
        assert users[0].id == user1.id
        assert users[1].id == user2.id
        assert users[0].score == 0
        assert users[0].n_correct_answers == 0
        assert users[0].n_wrong_answers == 0
        assert users[1].score == 1000
        assert users[1].n_correct_answers == 1
        assert users[1].n_wrong_answers == 0

        await application.store.games.update_game_scores(game.id, user1.id, [user2.id], 2000)
        users = await application.store.games.get_game_scores(game.id)
        assert len(users) == 2
        assert users[0].id == user1.id
        assert users[1].id == user2.id
        assert users[0].score == 2000
        assert users[0].n_correct_answers == 1
        assert users[0].n_wrong_answers == 0
        assert users[1].score == -1000
        assert users[1].n_correct_answers == 1
        assert users[1].n_wrong_answers == 1

        await application.store.games.update_game_scores(game.id, None, [user2.id, user1.id], 2000)
        users = await application.store.games.get_game_scores(game.id)
        assert len(users) == 2
        assert users[0].id == user1.id
        assert users[1].id == user2.id
        assert users[0].score == 0
        assert users[0].n_correct_answers == 1
        assert users[0].n_wrong_answers == 1
        assert users[1].score == -3000
        assert users[1].n_correct_answers == 1
        assert users[1].n_wrong_answers == 2

    async def test_get_remaining_questions(self, application, game):
        questions = await application.store.games.get_remaining_questions(game.id, 1)
        assert len(questions) == 3

        await application.store.games.set_question_asked(game.id, questions[1])
        questions = await application.store.games.get_remaining_questions(game.id, 1)
        assert len(questions) == 2
        assert questions[0].title == "title1"
        assert questions[1].title == "title3"

    @pytest.mark.parametrize("is_answered", [True, False])
    async def test_set_game_question_result(self, application, game, user1, user2, is_answered):
        questions = await application.store.games.get_remaining_questions(game.id, 1)
        question = questions[0]
        await application.store.games.set_question_asked(game.id, question)
        asked = await application.store.games.set_game_question_result(
            game.id, question.id, is_answered,
        )
        assert asked.game_id == game.id
        assert asked.question_id == question.id
        assert asked.is_answered is is_answered
        assert asked.is_done is True
