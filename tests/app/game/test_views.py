from app.game.models import GameStatsDC
from app.store.vk_api.responses import VKUser
from app.web.app import Application
from tests.fixtures.game import setup_game
from tests.utils import ok_response


async def make_played_game(application: Application,
                           chat_id: int,
                           user1: VKUser,
                           user2: VKUser,
                           question_ids: list[int]):
    game = await setup_game(application, chat_id, user1, user2)
    for index in question_ids:
        questions = await application.store.games.get_remaining_questions(game.id, 1)
        question = questions[index]
        await application.store.games.set_question_asked(game.id, question)
        await application.store.games.set_game_question_result(game.id, question.id, True)
        await application.store.games.update_game_scores(game.id, user1.id, [user2.id], 1000)
    await application.store.games.restore_status(chat_id)


class TestFetchGamesView:
    url = "/admin.fetch_games"

    async def test_success_empty(self, authed_cli):
        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=[])

    async def test_unauthorized(self, cli):
        response = await cli.get(self.url)
        assert response.status == 401

    async def test_success(self, authed_cli, application, chat_id, user1, user2):
        await make_played_game(application, chat_id, user1, user2, [])
        await make_played_game(application, chat_id, user1, user2, [2, 0])
        await make_played_game(application, chat_id, user1, user2, [1, 1, 0])

        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = (await response.json())["data"]
        assert len(data) == 3
        assert data[0]["id"] != data[1]["id"] != data[2]["id"]

        game = data[0]
        assert game["is_stopped"] is True
        assert game["finished_at"] is not None
        assert len(game["users"]) == 2
        assert game["users"][0]["score"] == 0
        assert game["users"][0]["n_correct_answers"] == 0
        assert game["users"][0]["n_wrong_answers"] == 0
        assert game["users"][1]["score"] == 0
        assert game["users"][1]["n_correct_answers"] == 0
        assert game["users"][1]["n_wrong_answers"] == 0

        game = data[1]
        assert game["is_stopped"] is True
        assert game["finished_at"] is not None
        assert len(game["users"]) == 2
        assert game["users"][0]["score"] == 2000
        assert game["users"][0]["n_correct_answers"] == 2
        assert game["users"][0]["n_wrong_answers"] == 0
        assert game["users"][1]["score"] == -2000
        assert game["users"][1]["n_correct_answers"] == 0
        assert game["users"][1]["n_wrong_answers"] == 2

        game = data[2]
        assert game["is_stopped"] is True
        assert game["finished_at"] is not None
        assert len(game["users"]) == 2
        assert game["users"][0]["score"] == 3000
        assert game["users"][0]["n_correct_answers"] == 3
        assert game["users"][0]["n_wrong_answers"] == 0
        assert game["users"][1]["score"] == -3000
        assert game["users"][1]["n_correct_answers"] == 0
        assert game["users"][1]["n_wrong_answers"] == 3

    async def test_pagination(self, authed_cli, application, chat_id, user1, user2):
        await make_played_game(application, chat_id, user1, user2, [])
        await make_played_game(application, chat_id, user1, user2, [2, 0])
        await make_played_game(application, chat_id, user1, user2, [1, 1, 0])

        response = await authed_cli.get(self.url, params={"page": 1})
        assert response.status == 200
        data = await response.json()
        assert len(data["data"]) == 3

        response = await authed_cli.get(self.url, params={"page": 2})
        assert response.status == 200
        data = await response.json()
        assert len(data["data"]) == 0

        response = await authed_cli.get(self.url, params={"page": 1, "per_page": 2})
        assert response.status == 200
        data = await response.json()
        assert len(data["data"]) == 2

        response = await authed_cli.get(self.url, params={"page": 2, "per_page": 2})
        assert response.status == 200
        data = await response.json()
        assert len(data["data"]) == 1

        response = await authed_cli.get(self.url, params={"page": 2, "per_page": 1})
        assert response.status == 200
        data = await response.json()
        assert len(data["data"]) == 1


class TestFetchGameStatsView:
    url = "/admin.fetch_game_stats"

    async def test_success_empty(self, authed_cli):
        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = await response.json()
        assert data == ok_response(data=GameStatsDC(games_total=0,
                                                    games_average_per_day=0.0,
                                                    duration_total=0,
                                                    duration_average=0.0,
                                                    top_winners=[],
                                                    top_scorers=[]).as_dict())

    async def test_unauthorized(self, cli):
        response = await cli.get(self.url)
        assert response.status == 401

    async def test_success(self, authed_cli, application, chat_id, user1, user2):
        await make_played_game(application, chat_id, user1, user2, [])
        await make_played_game(application, chat_id, user1, user2, [2, 0])
        await make_played_game(application, chat_id, user1, user2, [1, 1, 0])

        response = await authed_cli.get(self.url)
        assert response.status == 200
        data = (await response.json())["data"]
        assert data["games_total"] == 3
        assert data["games_average_per_day"] == 0.0
        assert data["duration_total"] < 5
        assert data["duration_average"] < 5.0
        assert len(data["top_winners"]) == 1
        assert len(data["top_scorers"]) == 2
        assert data["top_winners"][0]["id"] == user1.id
        assert data["top_winners"][0]["win_count"] == 3
        assert data["top_scorers"][0]["id"] == user1.id
        assert data["top_scorers"][0]["score"] == 3000
