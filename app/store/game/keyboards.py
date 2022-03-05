from app.store.game.payload import BotActions
from app.store.game.payload import (
    BasePayload, EmptyPayload, MainMenuPayload, CreateNewGamePayload, JoinUsersPayload,
    StartGamePayload, ChooseThemePayload, ChooseQuestionPayload,
    SendQuestionPayload, GetAnswerPayload, ShowAnswerPayload, StopGamePayload,
    ShowScoreboardPayload, GameRulesPayload, BotInfoPayload,
)
from app.store.vk_api.keyboard import Keyboard, CallbackButton, ButtonColor


def invite() -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("Поехали! 🤝🏻",
                           payload=MainMenuPayload(source=BotActions.invite, new=True),
                           color=ButtonColor.white),
        ],
    ])


def main_menu() -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("Старт 🚀",
                           payload=CreateNewGamePayload(),
                           color=ButtonColor.green),
        ],
        [
            CallbackButton("Правила игры",
                           payload=GameRulesPayload(),
                           color=ButtonColor.blue),
        ],
        [
            CallbackButton("О боте",
                           payload=BotInfoPayload(),
                           color=ButtonColor.blue),
        ],
        [
            CallbackButton("♻",
                           payload=MainMenuPayload(source=BotActions.main_menu, new=True),
                           color=ButtonColor.white),
        ],
    ])


def join_users() -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("Присоединиться",
                           payload=JoinUsersPayload(),
                           color=ButtonColor.blue),
        ],
        [
            CallbackButton("Старт",
                           payload=StartGamePayload(),
                           color=ButtonColor.green),
            CallbackButton("Отмена",
                           payload=MainMenuPayload(source=BotActions.join_users),
                           color=ButtonColor.red),
        ],
    ])


def question(game_id: int, who_s_turn: int) -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("🏅 Стоп 🏅",
                           payload=StopGamePayload(),
                           color=ButtonColor.red),
        ],
    ])


def results() -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("В главное меню",
                           payload=MainMenuPayload(source=BotActions.show_scoreboard, new=True),
                           color=ButtonColor.white),
        ],
    ])


def back(source: str) -> Keyboard:
    return Keyboard(inline=True, buttons=[
        [
            CallbackButton("Назад",
                           payload=MainMenuPayload(source=source),
                           color=ButtonColor.white),
        ],
    ])
