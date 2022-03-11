import asyncio
import random
import typing
from collections.abc import Callable, Awaitable
from dataclasses import dataclass
from functools import wraps
from typing import Optional

from app.base.accessor import BaseAccessor
from app.store.game import keyboards
from app.store.game.payload import (
    BasePayload, MainMenuPayload, CreateNewGamePayload, JoinUsersPayload,
    StartGamePayload, BaseGamePayload, ChooseThemePayload, ChooseQuestionPayload,
    SendQuestionPayload, GetAnswerPayload, ShowAnswerPayload, ConfirmStopGamePayload, StopGamePayload,
    ShowScoreboardPayload, GameRulesPayload, BotInfoPayload,
)
from app.store.game.payload import PRICES, Texts, Photos, Stickers, LINE_BREAK, PLUS_SIGN
from app.store.game.payload import UserCommands, BotActions
from app.store.vk_api.events import BaseEvent, ChatInviteRequest, MessageText, MessageCallback
from app.store.vk_api.keyboard import CallbackButton, Carousel, CarouselElement, Keyboard, ButtonColor
from app.utils import generate_uuid

if typing.TYPE_CHECKING:
    from app.web.app import Application

TypeCondition = Callable[[BaseEvent], bool]
TypeMessageFunc = Callable[[BaseEvent, BasePayload], Awaitable[None]]


@dataclass
class EventSubscriber:
    condition: TypeCondition
    func: TypeMessageFunc


def dummy_condition(_: BaseEvent) -> bool:
    return True


class VKBot(BaseAccessor):
    gc_task: asyncio.Task

    def __init__(self, app: "Application"):
        super(VKBot, self).__init__(app)
        self.chat_invite_request_subscribers: list[EventSubscriber] = []
        self.message_text_subscribers: list[EventSubscriber] = []
        self.message_callback_subscribers: list[EventSubscriber] = []
        self.tasks: dict[str, asyncio.Task] = {}
        self.is_running = False

    async def connect(self, app: "Application"):
        register_bot_actions(self)
        self.is_running = True
        self.gc_task = asyncio.create_task(self.garbage_collector())

    async def disconnect(self, app: "Application"):
        self.is_running = False
        await self.gc_task

    async def garbage_collector(self):
        seconds = self.app.config.vk_bot.bot_gc_sleep
        while self.is_running:
            for uid in list(self.tasks.keys()):
                task = self.tasks.get(uid)
                if task.done() or task.cancelled():
                    del self.tasks[uid]
            await asyncio.sleep(seconds)

    async def schedule_task(self, uid: str, coro: Awaitable[None], delay=0.0):
        async def task():
            if delay > 0.0:
                await asyncio.sleep(delay)
            await coro

        self.tasks[uid] = asyncio.create_task(task())

    async def cancel_task(self, uid: str):
        task = self.tasks.get(uid)
        if task:
            task.cancel()

    def on_chat_invite_request(self, condition: Optional[TypeCondition] = None):
        condition = condition or dummy_condition

        def decorator(func: TypeMessageFunc):
            self.chat_invite_request_subscribers.append(
                EventSubscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(msg: MessageCallback, payload: BasePayload):
                return await func(msg, payload)

            return wrapper

        return decorator

    def on_message_text(self, condition: Optional[TypeCondition] = None):
        condition = condition or dummy_condition

        def decorator(func: TypeMessageFunc):
            self.message_text_subscribers.append(
                EventSubscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(msg: MessageCallback, payload: BasePayload):
                return await func(msg, payload)

            return wrapper

        return decorator

    def on_message_callback(self, condition: Optional[TypeCondition] = None):
        condition = condition or dummy_condition

        def decorator(func: TypeMessageFunc):
            self.message_callback_subscribers.append(
                EventSubscriber(condition=condition, func=func)
            )

            @wraps(func)
            async def wrapper(msg: MessageCallback, payload: BasePayload):
                return await func(msg, payload)

            return wrapper

        return decorator

    async def handle_event(self, event: BaseEvent) -> None:
        if isinstance(event, ChatInviteRequest):
            if self.app.store.states.is_flood_detected(event.chat_id):
                return
            for subscriber in self.chat_invite_request_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event, event.payload)
        elif isinstance(event, MessageText):
            if self.app.store.states.is_flood_detected(event.chat_id):
                return
            for subscriber in self.message_text_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event, event.payload)
        elif isinstance(event, MessageCallback):
            if self.app.store.states.is_flood_detected(event.chat_id):
                return await event.show_snackbar(Texts.flood_detected)
            for subscriber in self.message_callback_subscribers:
                if subscriber.condition(event):
                    return await subscriber.func(event, event.payload)
        else:
            self.app.logger.warning(f"unknown event: {event}")


def register_bot_actions(bot: VKBot):
    bot.on_chat_invite_request()(invite)

    bot.on_message_text(lambda i: i.text.lower() == UserCommands.start)(invite)

    bot.on_message_callback(lambda i: i.payload.action == BotActions.main_menu)(main_menu)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.create_new_game)(create_new_game)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.join_users)(join_users)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.start_game)(start_game)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.choose_theme)(choose_theme)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.choose_question)(choose_question)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.send_question)(send_question)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.get_answer)(get_answer)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.show_scoreboard)(show_scoreboard)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.confirm_stop_game)(confirm_stop_game)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.stop_game)(stop_game)

    bot.on_message_callback(lambda i: i.payload.action == BotActions.game_rules)(game_rules)
    bot.on_message_callback(lambda i: i.payload.action == BotActions.bot_info)(bot_info)


def filter_game_id(func: TypeMessageFunc):
    @wraps(func)
    async def wrapper(msg: MessageCallback, payload: BaseGamePayload):
        if msg.states.get_game_id(msg.chat_id) != payload.game_id:
            return await msg.show_snackbar(Texts.old_game_round)
        return await func(msg, payload)

    return wrapper


def filter_who_s_turn(func: TypeMessageFunc):
    @wraps(func)
    async def wrapper(msg: MessageCallback, payload: BaseGamePayload):
        if msg.states.get_who_s_turn(msg.chat_id) != msg.user_id:
            return await msg.show_snackbar(Texts.not_your_turn)
        return await func(msg, payload)

    return wrapper


async def invite(msg: ChatInviteRequest, _: BasePayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) == BotActions.invite:
            return
        msg.states.set_game_status(msg.chat_id, BotActions.invite)

    await msg.games.joined_the_chat(msg.chat_id)
    await msg.send(attachment=Photos.main_wallpaper, keyboard=keyboards.invite())


async def main_menu(msg: MessageCallback, payload: MainMenuPayload):
    async with msg.states.locks.game_status:
        if payload.source != BotActions.main_menu:
            if msg.states.get_game_status(msg.chat_id) == BotActions.main_menu:
                return
        msg.states.restore_status(msg.chat_id)

    await msg.games.restore_status(msg.chat_id)
    if payload.new:
        if payload.source == BotActions.main_menu:
            await msg.edit(Texts.goodbye)
        else:
            await msg.edit(msg.states.get_previous_text(msg.chat_id))
        await msg.send(attachment=Photos.main_wallpaper, keyboard=keyboards.main_menu())
    else:
        await msg.edit(attachment=Photos.main_wallpaper, keyboard=keyboards.main_menu())


async def game_rules(msg: MessageCallback, _: GameRulesPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) == BotActions.game_rules:
            return
        msg.states.set_game_status(msg.chat_id, BotActions.game_rules)
    await msg.edit(Texts.rules, keyboard=keyboards.back(source=BotActions.game_rules))


async def bot_info(msg: MessageCallback, _: BotInfoPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) == BotActions.bot_info:
            return
        msg.states.set_game_status(msg.chat_id, BotActions.bot_info)
    await msg.edit(Texts.about, keyboard=keyboards.back(source=BotActions.bot_info))


async def create_new_game(msg: MessageCallback, _: CreateNewGamePayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.main_menu:
            return await msg.show_snackbar(Texts.game_is_already_started)
        msg.states.set_game_status(msg.chat_id, BotActions.join_users)

    text = f"Присоединились к игре:{LINE_BREAK}😥 Пока никого..."
    await msg.edit(text, keyboard=keyboards.join_users())


async def join_users(msg: MessageCallback, _: JoinUsersPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.join_users:
            return await msg.show_snackbar(Texts.game_is_already_started)

    async with msg.states.locks.game_users:
        users = msg.states.get_joined_users(msg.chat_id)
        if any(msg.user_id == u.id for u in users):
            return await msg.show_snackbar(Texts.you_are_already_joined)

        new_user = await msg.get_user_info()
        if new_user is None:
            return await msg.show_snackbar(Texts.error_try_again)
        msg.states.set_user_info(new_user)

        users.append(new_user)
        msg.states.set_users_joined(msg.chat_id, users)

    text = f"Присоединились к игре:{LINE_BREAK}"
    text += LINE_BREAK.join(f"👤 {u.first_name} {u.last_name}" for i, u in enumerate(users))
    await msg.edit(text, keyboard=keyboards.join_users())


async def start_game(msg: MessageCallback, _: StartGamePayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.join_users:
            return await msg.show_snackbar(Texts.game_is_already_started)
        users = msg.states.get_joined_users(msg.chat_id)
        if not users:
            return await msg.show_snackbar(Texts.nobody_joined)
        if not any(msg.user_id == u.id for u in users):
            return await msg.show_snackbar(Texts.firstly_join_the_game)
        msg.states.set_game_status(msg.chat_id, BotActions.choose_theme)

    user_dcs = await msg.games.create_users(users)
    game_dc = await msg.games.create_game(msg.chat_id, user_dcs)
    msg.states.set_game_id(msg.chat_id, game_dc.id)
    msg.states.set_who_s_turn(msg.chat_id, msg.user_id)

    await choose_theme(msg, ChooseThemePayload(game_id=game_dc.id, new=True))


@filter_game_id
async def choose_theme(msg: MessageCallback, payload: ChooseThemePayload):
    # на view выбора темы может перейти любой пользователь,
    # но выбирать саму тему может только тот, чья сейчас очередь
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.choose_theme:
            return await msg.show_snackbar(Texts.old_game_round)
        msg.states.set_game_status(msg.chat_id, BotActions.choose_question)

    themes = await msg.quiz.list_themes()
    theme_chosen_prices = msg.states.get_theme_chosen_prices(msg.chat_id)
    exclude_theme_ids = [k for k, v in theme_chosen_prices.items() if 0 not in v]
    themes = [i for i in themes if i.id not in exclude_theme_ids]

    if not themes:  # все вопросы исчерпаны, конец игры
        return await stop_game(msg, StopGamePayload(game_id=payload.game_id, new=True))

    carousel = Carousel()
    for theme in themes:
        element = CarouselElement(
            title=theme.title,
            description=theme.title,
            photo_id=Photos.theme_carousel,
            buttons=[
                CallbackButton("Выбрать", payload=ChooseQuestionPayload(game_id=payload.game_id,
                                                                        theme_id=theme.id,
                                                                        theme_title=theme.title))
            ])
        carousel.add_element(element)

    user = msg.states.get_user_info(msg.states.get_who_s_turn(msg.chat_id))
    if payload.new:
        await msg.edit(msg.states.get_previous_text(msg.chat_id))
        await msg.send(f"👉🏻 {user.name}, выберите тему:", carousel=carousel)
    else:
        await msg.edit(f"👉🏻 {user.name}, выберите тему:", carousel=carousel)


@filter_game_id
@filter_who_s_turn
async def choose_question(msg: MessageCallback, payload: ChooseQuestionPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.choose_question:
            return await msg.show_snackbar(Texts.old_game_round)
        msg.states.set_game_status(msg.chat_id, BotActions.send_question)

    # всего 5 вопросов в теме, 1 = вопрос уже выбран ранее
    chosen_prices = msg.states.get_theme_chosen_prices(msg.chat_id).get(payload.theme_id, [0] * 5)
    button_texts = iter(str(p) if c == 0 else "--" for c, p in zip(chosen_prices, PRICES))
    button_prices = iter(p if c == 0 else 0 for c, p in zip(chosen_prices, PRICES))
    button_colors = iter(ButtonColor.blue if c == 0 else ButtonColor.white for c in chosen_prices)

    def get_button() -> CallbackButton:
        return CallbackButton(next(button_texts),
                              payload=SendQuestionPayload(game_id=payload.game_id,
                                                          theme_id=payload.theme_id,
                                                          price=next(button_prices)),
                              color=next(button_colors))

    keyboard = Keyboard(inline=True, buttons=[
        [get_button(), get_button(), get_button()],
        [get_button(), get_button()],
    ])

    await msg.edit(f"Тема:{LINE_BREAK}📗 {payload.theme_title}")

    user = msg.states.get_user_info(msg.user_id)
    await msg.send(f"👉🏻 {user.name}, выберите вопрос:", keyboard=keyboard)


@filter_game_id
@filter_who_s_turn
async def send_question(msg: MessageCallback, payload: SendQuestionPayload):
    if payload.price == 0:
        return await msg.event_ok()

    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.send_question:
            return await msg.show_snackbar(Texts.old_game_round)
        msg.states.set_game_status(msg.chat_id, BotActions.get_answer)

    # всего 5 вопросов в теме, 1 = вопрос уже выбран ранее
    theme_chosen_prices = msg.states.get_theme_chosen_prices(msg.chat_id)
    chosen_prices = theme_chosen_prices.get(payload.theme_id, [0] * 5)
    chosen_prices[PRICES.index(payload.price)] = 1
    theme_chosen_prices[payload.theme_id] = chosen_prices
    msg.states.set_theme_chosen_prices(msg.chat_id, theme_chosen_prices)

    question_models = await msg.games.get_remaining_questions(payload.game_id, payload.theme_id)
    question = random.choice(question_models).as_dataclass()
    await msg.games.set_question_asked(payload.game_id, question)
    random.shuffle(question.answers)
    msg.states.set_current_question_id(msg.chat_id, question.id)
    msg.states.set_current_answer(msg.chat_id, [i for i in question.answers if i.is_correct][0])
    msg.states.set_current_price(msg.chat_id, payload.price)

    text = f"Вопрос на {payload.price} очков:{LINE_BREAK}{LINE_BREAK}" \
           f"🔎 {question.title}{LINE_BREAK}{LINE_BREAK}"
    answers = iter(i.title for i in question.answers)
    task_uid = generate_uuid()

    def get_button() -> CallbackButton:
        answer = next(answers)
        return CallbackButton(answer[:40],
                              payload=GetAnswerPayload(game_id=payload.game_id,
                                                       question=question.title,
                                                       answer=answer,
                                                       uid=task_uid),
                              color=ButtonColor.white)

    keyboard = Keyboard(inline=True, buttons=[
        [get_button()],
        [get_button()],
        [get_button()],
        [get_button()],
    ])

    if msg.app.config.vk_bot.animate_timer:
        for i in range(msg.app.config.vk_bot.sleep_before_show_variants, 0, -1):
            await msg.edit(text + f"⏱ {i}...")
            await asyncio.sleep(1.0)
    else:
        await msg.edit(text)
        await asyncio.sleep(msg.app.config.vk_bot.sleep_before_show_variants)

    async def timer():
        if msg.app.config.vk_bot.animate_timer:
            for i in range(msg.app.config.vk_bot.sleep_before_show_answer, 0, -1):
                await msg.edit(text + f"⏱ {i}...", keyboard=keyboard)
                await asyncio.sleep(1.0)
        else:
            await msg.edit(text, keyboard=keyboard)
            await asyncio.sleep(msg.app.config.vk_bot.sleep_before_show_answer)

        async with msg.states.locks.game_status:
            if msg.states.get_game_status(msg.chat_id) == BotActions.get_answer:
                msg.states.set_game_status(msg.chat_id, BotActions.show_answer)

        await show_answer(msg, ShowAnswerPayload(game_id=payload.game_id,
                                                 question=question.title,
                                                 winner=None))

    await msg.app.store.vk_bot.schedule_task(task_uid, timer())


@filter_game_id
async def get_answer(msg: MessageCallback, payload: GetAnswerPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.get_answer:
            return await msg.show_snackbar(Texts.too_late)
        answered_users = msg.states.get_answered_users(msg.chat_id)
        if msg.user_id in answered_users:
            return await msg.show_snackbar(Texts.you_are_already_answered)
        answered_users.append(msg.user_id)
        msg.states.set_users_answered(msg.chat_id, answered_users)
        if msg.states.get_current_answer(msg.chat_id).title != payload.answer:
            return await msg.event_ok()
        msg.states.set_game_status(msg.chat_id, BotActions.show_answer)

    await msg.app.store.vk_bot.cancel_task(payload.uid)
    await show_answer(msg, ShowAnswerPayload(game_id=payload.game_id,
                                             question=payload.question,
                                             winner=msg.user_id))


@filter_game_id
async def show_answer(msg: MessageCallback, payload: ShowAnswerPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.show_answer:
            return await msg.show_snackbar(Texts.too_late)
        msg.states.set_game_status(msg.chat_id, BotActions.show_scoreboard)

    await msg.edit(f"Вопрос:{LINE_BREAK}🔎 {payload.question}")
    await msg.send(sticker_id=Stickers.dog_wait_sec)
    await asyncio.sleep(2.0)

    current_price = msg.states.get_current_price(msg.chat_id)
    answered_users_ids = msg.states.get_answered_users(msg.chat_id)
    wrong_answered_users_ids = [i for i in answered_users_ids if i != payload.winner]
    await msg.games.update_game_scores(payload.game_id,
                                       payload.winner,
                                       wrong_answered_users_ids,
                                       current_price)

    question_id = msg.states.get_current_question_id(msg.chat_id)
    await msg.games.set_game_question_result(payload.game_id,
                                             question_id,
                                             is_answered=payload.winner is not None)

    answer = msg.states.get_current_answer(msg.chat_id)
    await msg.send(f"Правильный ответ:{LINE_BREAK}💡 {answer.title}{LINE_BREAK}📖 {answer.description}")

    text = ""
    if payload.winner is None:
        users = msg.states.get_joined_users(msg.chat_id)
        who_s_turn = random.choice(users).id
    else:
        who_s_turn = payload.winner
        user = msg.states.get_user_info(payload.winner)
        # знак "+" удаляется при отправке в ВК
        text += f"💪🏻 {user.name}: {PLUS_SIGN}{current_price}{LINE_BREAK}"

    msg.states.set_who_s_turn(msg.chat_id, who_s_turn)
    for user_id in wrong_answered_users_ids:
        user = msg.states.get_user_info(user_id)
        text += f"😥 {user.name}: -{current_price}{LINE_BREAK}"

    if not text:
        text = "Ответов не поступило... 💤"
    await msg.send(f"Итоги раунда:{LINE_BREAK}" + text)

    msg.states.question_ended(msg.chat_id)
    await show_scoreboard(msg, ShowScoreboardPayload(game_id=payload.game_id, new=True))


@filter_game_id
async def show_scoreboard(msg: MessageCallback, payload: ShowScoreboardPayload):
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) != BotActions.show_scoreboard:
            return await msg.show_snackbar(Texts.old_game_round)
        msg.states.set_game_status(msg.chat_id, BotActions.choose_theme)

    scores = await msg.games.get_game_scores(payload.game_id)
    scores.sort(key=lambda i: i.score, reverse=True)

    text = f"Топ 5 игроков:{LINE_BREAK}"
    for user in scores[:5]:
        text += f"👤 {user.first_name} {user.last_name}: {user.score} " \
                f"({user.n_correct_answers}:{user.n_wrong_answers}){LINE_BREAK}"

    keyboard = Keyboard(inline=True, buttons=[
        [CallbackButton("👍🏻 Дальше",
                        payload=ChooseThemePayload(game_id=payload.game_id, new=True),
                        color=ButtonColor.green)],
        [CallbackButton("⛔ Завершить игру",
                        payload=ConfirmStopGamePayload(game_id=payload.game_id),
                        color=ButtonColor.red)],
    ])

    if payload.new:
        await msg.send(text, keyboard=keyboard)
    else:
        await msg.edit(text, keyboard=keyboard)


@filter_game_id
async def confirm_stop_game(msg: MessageCallback, payload: ConfirmStopGamePayload):
    # остановить игру может любой пользователь
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) == BotActions.show_scoreboard:
            return await msg.show_snackbar(Texts.too_late)
        msg.states.set_game_status(msg.chat_id, BotActions.show_scoreboard)

    await msg.delete()
    await msg.send("Завершить игру?", keyboard=Keyboard(inline=True, buttons=[
        [
            CallbackButton("Да",
                           payload=StopGamePayload(game_id=payload.game_id, new=False),
                           color=ButtonColor.red),
            CallbackButton("Нет",
                           payload=ShowScoreboardPayload(game_id=payload.game_id, new=False),
                           color=ButtonColor.green),
        ]
    ]))


@filter_game_id
async def stop_game(msg: MessageCallback, payload: StopGamePayload):
    # остановить игру может любой пользователь
    async with msg.states.locks.game_status:
        if msg.states.get_game_status(msg.chat_id) == BotActions.game_finished:
            return await msg.show_snackbar(Texts.game_is_already_stopped)
        msg.states.set_game_status(msg.chat_id, BotActions.game_finished)

    users = await msg.games.get_game_scores(payload.game_id)
    users.sort(key=lambda i: i.score, reverse=True)

    medals = "🥇🥈🥉" + "👤" * max(0, len(users) - 3)
    text = f"Итоговые результаты:{LINE_BREAK}"
    for user, medal in zip(users, medals):
        text += f"{medal} {user.first_name} {user.last_name}: {user.score} " \
                f"({user.n_correct_answers}:{user.n_wrong_answers}){LINE_BREAK}{LINE_BREAK}"

    if payload.new:
        await msg.edit(msg.states.get_previous_text(msg.chat_id))
        await msg.send(text, keyboard=keyboards.final_results())
    else:
        await msg.edit(text, keyboard=keyboards.final_results())
