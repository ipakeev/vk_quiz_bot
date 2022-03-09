import pathlib
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from aiohttp.test_utils import TestClient, loop_context

import app.store.vk_api.bot
import app.store.vk_api.long_poller
import app.store.vk_api.messenger
import app.store.vk_api.updates_poller
from app.store.store import Store
from app.web.app import setup_app, Application
from app.web.config import Config


@pytest.fixture(scope="session")
def loop():
    with loop_context() as _loop:
        yield _loop


@pytest.fixture(scope="session", autouse=True)
def vk_bot():
    with patch("app.store.vk_api.bot.VKBot",
               AsyncMock(spec=app.store.vk_api.bot.VKBot)):
        yield


@pytest.fixture(scope="session", autouse=True)
def vk_long_poller():
    with patch("app.store.vk_api.long_poller.VKLongPoller",
               AsyncMock(spec=app.store.vk_api.long_poller.VKLongPoller)):
        yield


@pytest.fixture(scope="session", autouse=True)
def vk_messenger():
    with patch("app.store.vk_api.messenger.VKMessenger",
               AsyncMock(spec=app.store.vk_api.messenger.VKMessenger)):
        yield


@pytest.fixture(scope="session", autouse=True)
def vk_updates_poller():
    with patch("app.store.vk_api.updates_poller.VKUpdatesPoller",
               AsyncMock(spec=app.store.vk_api.updates_poller.VKUpdatesPoller)):
        yield


@pytest.fixture(scope="session", autouse=True)
def vk_updates_poller():
    with patch("app.store.vk_api.updates_poller.VKUpdatesPoller",
               AsyncMock(spec=app.store.vk_api.updates_poller.VKUpdatesPoller)):
        yield


@pytest.fixture(scope="session")
def server() -> Application:
    config_file = pathlib.Path(__file__).resolve().parent / "config.yaml"
    _app = setup_app(config_file)
    return _app


@pytest.fixture
def store(server) -> Store:
    return server.store


@pytest.fixture
def config(server) -> Config:
    return server.config


@pytest.fixture(autouse=True)
def cli(aiohttp_client, loop, server) -> TestClient:
    client = loop.run_until_complete(aiohttp_client(server))
    yield client
    loop.run_until_complete(clear_db(server))


@pytest.fixture
async def authed_cli(cli, config) -> TestClient:
    await cli.post(
        "/admin.login",
        data={
            "email": config.admin.email,
            "password": config.admin.password,
        },
    )
    yield cli


async def clear_db(server):
    db = server.database.db
    for table in db.sorted_tables:
        await db.status(db.text(f"TRUNCATE {table.name} CASCADE"))
        await db.status(db.text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH 1"))
