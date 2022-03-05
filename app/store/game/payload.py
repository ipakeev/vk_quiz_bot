from dataclasses import dataclass
from typing import Optional

LINE_BREAK = "%0A"

PRICES = [500, 1000, 1500, 2000, 2500]


class UserCommands:
    start = "/start"


class BotActions:
    empty = "empty"
    invite = "invite"
    main_menu = "main_menu"
    create_new_game = "create_new_game"
    join_users = "join_users"
    start_game = "start_game"
    choose_theme = "choose_theme"
    choose_question = "choose_question"
    send_question = "send_question"
    get_answer = "get_answer"
    show_answer = "show_answer"
    show_scoreboard = "show_scoreboard"
    stop_game = "stop_game"
    game_rules = "game_rules"
    bot_info = "bot_info"


class Stickers:
    cat_hello = 51117


class Photos:
    theme_carousel = "-210566950_457239018"


class Texts:
    invite = f"""Благодарю за приглашение в чат.{LINE_BREAK}
Я - бот для игры в викторину.{LINE_BREAK}
Я создан для того, чтобы весело проводить время с друзьями.{LINE_BREAK}
Желаю приятной игры."""
    main_menu = "Главное меню"
    goodbye = "🗿"

    game_is_already_started = "Игра уже началась."
    you_are_already_joined = "Вы уже присоединились к игре."
    nobody_joined = "Никто не присоединился к игре."
    firstly_join_the_game = "Сначала присоединитесь к игре."
    error_try_again = "Произошла ошибка. Повторите ещё раз."
    not_your_turn = "Сейчас не ваша очередь."
    old_game_round = "Этот раунд игры устарел."
    too_late = "Опоздали..."
    you_are_already_answered = "Вы уже ответили."


@dataclass
class BasePayload:

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EmptyPayload(BasePayload):
    action: str = BotActions.empty


@dataclass
class MainMenuPayload(BasePayload):
    source: str
    new: bool = False
    action: str = BotActions.main_menu


@dataclass
class CreateNewGamePayload(BasePayload):
    action: str = BotActions.create_new_game


@dataclass
class JoinUsersPayload(BasePayload):
    action: str = BotActions.join_users


@dataclass
class StartGamePayload(BasePayload):
    action: str = BotActions.start_game


@dataclass
class ChooseThemePayload(BasePayload):
    game_id: int
    new: bool = False
    action: str = BotActions.choose_theme


@dataclass
class ChooseQuestionPayload(BasePayload):
    game_id: int
    theme_id: int
    theme_title: str
    action: str = BotActions.choose_question


@dataclass
class SendQuestionPayload(BasePayload):
    game_id: int
    theme_id: int
    price: int
    action: str = BotActions.send_question


@dataclass
class GetAnswerPayload(BasePayload):
    game_id: int
    question: str
    answer: str
    uid: str
    action: str = BotActions.get_answer


@dataclass
class ShowAnswerPayload(BasePayload):
    game_id: int
    question: str
    winner: Optional[int] = None
    action: str = BotActions.show_answer


@dataclass
class ShowScoreboardPayload(BasePayload):
    game_id: int
    action: str = BotActions.show_scoreboard


@dataclass
class StopGamePayload(BasePayload):
    game_id: int
    action: str = BotActions.stop_game


@dataclass
class GameRulesPayload(BasePayload):
    action: str = BotActions.game_rules


@dataclass
class BotInfoPayload(BasePayload):
    action: str = BotActions.bot_info


class PayloadFactory:

    @classmethod
    def create(cls, payload: dict) -> BasePayload:
        action = payload.get("action")
        if action == BotActions.main_menu:
            return MainMenuPayload(source=payload["source"],
                                   new=payload.get("new", False))
        elif action == BotActions.create_new_game:
            return CreateNewGamePayload()
        elif action == BotActions.join_users:
            return JoinUsersPayload()
        elif action == BotActions.start_game:
            return StartGamePayload()
        elif action == BotActions.choose_theme:
            return ChooseThemePayload(game_id=payload["game_id"],
                                      new=payload.get("new", False))
        elif action == BotActions.choose_question:
            return ChooseQuestionPayload(game_id=payload["game_id"],
                                         theme_id=payload["theme_id"],
                                         theme_title=payload["theme_title"])
        elif action == BotActions.send_question:
            return SendQuestionPayload(game_id=payload["game_id"],
                                       theme_id=payload["theme_id"],
                                       price=payload["price"])
        elif action == BotActions.get_answer:
            return GetAnswerPayload(game_id=payload["game_id"],
                                    question=payload["question"],
                                    answer=payload["answer"],
                                    uid=payload["uid"])
        elif action == BotActions.show_answer:
            return ShowAnswerPayload(game_id=payload["game_id"],
                                     question=payload["question"],
                                     winner=payload.get('winner'))
        elif action == BotActions.show_scoreboard:
            return ShowScoreboardPayload(game_id=payload["game_id"])
        elif action == BotActions.stop_game:
            return StopGamePayload(game_id=payload["game_id"])
        elif action == BotActions.game_rules:
            return GameRulesPayload()
        elif action == BotActions.bot_info:
            return BotInfoPayload()
        else:
            return EmptyPayload()
