import json
import random
from typing import Optional

from redis import Redis
from sqlalchemy import and_, not_
from sqlalchemy.dialects.postgresql import insert

from app.base.accessor import BaseAccessor
from app.game.models import (
    UserDC, UserModel,
    ChatModel,
    GameModel, GameAskedQuestionModel, CorrectAnswerModel, GameUserScoreModel
)
from app.quiz.models import QuestionDC, QuestionModel, AnswerModel, AnswerDC
from app.store.game.payload import BotActions
from app.store.vk_api.responses import VKUser
from app.web.app import Application


class StateAccessor(BaseAccessor):
    redis: Redis

    async def connect(self, app: "Application"):
        self.redis = app.database.redis

    def restore_status(self, chat_id: int) -> None:
        self.redis.set(f"game_status_{chat_id}", BotActions.main_menu)
        self.redis.delete(f"game_id_{chat_id}")
        self.redis.delete(f"game_users_{chat_id}")
        self.redis.delete(f"who_s_turn_{chat_id}")
        self.redis.delete(f"game_prices_{chat_id}")
        self.redis.delete(f"current_question_id_{chat_id}")
        self.question_ended(chat_id)

    def set_game_id(self, chat_id: int, game_id: int) -> None:
        self.redis.set(f"game_id_{chat_id}", game_id)

    def get_game_id(self, chat_id: int) -> Optional[int]:
        value = self.redis.get(f"game_id_{chat_id}")
        if value is None:
            return None
        return int(value.decode())

    def set_game_status(self, chat_id: int, status: str) -> None:
        self.redis.set(f"game_status_{chat_id}", status)

    def get_game_status(self, chat_id: int) -> str:
        return self.app.database.redis.get(f"game_status_{chat_id}").decode()

    def set_users_joined(self, chat_id: int, users: list[VKUser]) -> None:
        self.redis.set(
            f"game_users_{chat_id}",
            json.dumps([i.as_dict() for i in users], ensure_ascii=False)
        )

    def get_joined_users(self, chat_id: int) -> list[VKUser]:
        value = self.redis.get(f"game_users_{chat_id}")
        if not value:
            return []
        return [VKUser(i) for i in json.loads(value.decode())]

    def set_user_info(self, user: VKUser) -> None:
        self.redis.set(f"user_{user.id}", json.dumps(user.as_dict(), ensure_ascii=False))

    def get_user_info(self, user_id: int) -> VKUser:
        value = self.redis.get(f"user_{user_id}")
        return VKUser(json.loads(value.decode()))

    def set_who_s_turn(self, chat_id: int, user_id: int) -> None:
        self.redis.set(f"who_s_turn_{chat_id}", user_id)

    def get_who_s_turn(self, chat_id: int) -> int:
        value = self.redis.get(f"who_s_turn_{chat_id}")
        return int(value.decode())

    def set_theme_chosen_prices(self, chat_id: int, prices: dict[int, list[int]]) -> None:
        self.redis.set(f"game_prices_{chat_id}", json.dumps(prices))

    def get_theme_chosen_prices(self, chat_id) -> dict[int, list[int]]:
        value = self.redis.get(f"game_prices_{chat_id}")
        if not value:
            return {}
        return {int(k): v for k, v in json.loads(value.decode()).items()}

    def set_current_question_id(self, chat_id: int, question_id: int) -> None:
        self.redis.set(f"current_question_id_{chat_id}", question_id)

    def get_current_question_id(self, chat_id: int) -> int:
        return int(self.redis.get(f"current_question_id_{chat_id}").decode())

    def set_current_price(self, chat_id: int, price: int) -> None:
        self.redis.set(f"current_price_{chat_id}", price)

    def get_current_price(self, chat_id: int) -> int:
        return int(self.redis.get(f"current_price_{chat_id}").decode())

    def set_current_answer(self, chat_id: int, answer: AnswerDC) -> None:
        self.redis.set(f"current_answer_{chat_id}", json.dumps(answer.as_dict(), ensure_ascii=False))

    def get_current_answer(self, chat_id: int) -> AnswerDC:
        value = self.redis.get(f"current_answer_{chat_id}")
        return AnswerDC(**json.loads(value.decode()))

    def set_users_answered(self, chat_id: int, users: list[int]) -> None:
        self.redis.set(f"users_answered_{chat_id}", json.dumps(users))

    def get_answered_users(self, chat_id: int) -> list[int]:
        value = self.redis.get(f"users_answered_{chat_id}")
        if not value:
            return []
        return json.loads(value.decode())

    def question_ended(self, chat_id: int) -> None:
        self.redis.delete(f"current_price_{chat_id}")
        self.redis.delete(f"current_answer_{chat_id}")
        self.redis.delete(f"users_answered_{chat_id}")

    def set_previous_text(self, chat_id: int, text: str) -> None:
        self.redis.set(f"text_{chat_id}", text)

    def get_previous_text(self, chat_id: int) -> str:
        return self.redis.get(f"text_{chat_id}").decode()


class GameAccessor(BaseAccessor):

    async def restore_status(self, chat_id: int) -> None:
        game_models: list[GameModel] = await GameModel.update \
            .values(is_stopped=True) \
            .where(GameModel.chat_id == chat_id) \
            .returning(*GameModel).gino.all()
        if not game_models:
            return
        await GameAskedQuestionModel.update.values(is_done=True) \
            .where(GameAskedQuestionModel.game_id.in_([i.id for i in game_models])) \
            .gino.status()

    async def create_users(self, users: list[UserDC]) -> list[UserModel]:
        stmt = insert(UserModel).values(
            [dict(id=i.id, first_name=i.first_name, last_name=i.last_name) for i in users]
        )
        query = stmt.on_conflict_do_update(
            index_elements=[UserModel.id],
            set_=dict(first_name=stmt.excluded.first_name,
                      last_name=stmt.excluded.last_name)
        ).returning(*UserModel)
        return await query.gino.model(UserModel).all()

    async def joined_the_chat(self, chat_id: int) -> None:
        await insert(ChatModel).values(id=chat_id).on_conflict_do_nothing().gino.status()

    async def create_game(self, chat_id, users: list[UserModel]) -> GameModel:
        game: GameModel = await GameModel.create(chat_id=chat_id)
        await GameUserScoreModel.insert().gino.all(
            *(dict(game_id=game.id, user_id=u.id) for u in users)
        )
        return game

    async def update_game_user_score(self, game_id: int, user_id: int, score: int):
        user_score: GameUserScoreModel = await GameUserScoreModel.query.where(
            and_(GameUserScoreModel.game_id == game_id,
                 GameUserScoreModel.user_id == user_id)
        ).gino.first()
        await user_score.update(score=user_score.score + score).apply()

    async def get_new_question(self, game_id: int, theme_id: int) -> QuestionDC:
        exclude_questions = GameAskedQuestionModel.select("question_id") \
            .where(GameAskedQuestionModel.game_id == game_id)

        questions: list[QuestionModel] = await QuestionModel \
            .outerjoin(AnswerModel, QuestionModel.id == AnswerModel.question_id) \
            .select() \
            .where(and_(
            QuestionModel.theme_id == theme_id,
            not_(QuestionModel.id.in_(exclude_questions)),
        )) \
            .gino.load(
            QuestionModel.distinct(QuestionModel.id).load(
                answers=AnswerModel.load()
            )
        ).all()

        question: QuestionModel = random.choice(questions)
        await GameAskedQuestionModel.create(game_id=game_id, question_id=question.id)
        return question.as_dataclass()

    async def set_game_question_result(self,
                                       game_id: int,
                                       question_id: int,
                                       is_answered: bool,
                                       user_id: Optional[int] = None) -> None:
        await GameAskedQuestionModel.update.values(is_answered=is_answered, is_done=True).where(
            and_(GameAskedQuestionModel.game_id == game_id,
                 GameAskedQuestionModel.question_id == question_id)
        ).gino.status()

        if user_id is not None:
            await CorrectAnswerModel.create(game_id=game_id, question_id=question_id, user_id=user_id)

    async def get_game_scores(self, game_id: int) -> list[UserDC]:
        query = UserModel.join(
            GameUserScoreModel, and_(UserModel.id == GameUserScoreModel.user_id,
                                     GameUserScoreModel.game_id == game_id)
        ).join(
            CorrectAnswerModel, and_(UserModel.id == CorrectAnswerModel.user_id,
                                     GameUserScoreModel.game_id == game_id)
        ).select()
        user_models: list[UserModel] = await query.gino.load(
            UserModel.distinct(UserModel.id).load(
                correct_answers=CorrectAnswerModel.load(),
                score=GameUserScoreModel.score,
            )
        ).all()
        return [UserDC(id=i.id,
                       first_name=i.first_name,
                       last_name=i.last_name,
                       score=i.score,
                       n_correct_answers=len(i.correct_answers)) for i in user_models]
