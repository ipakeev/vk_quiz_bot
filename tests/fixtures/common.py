import pathlib
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import TestClient, loop_context

import app.store.vk_api.bot
import app.store.vk_api.long_poller
import app.store.vk_api.messenger
import app.store.vk_api.updates_poller
from app.web.app import setup_app, Application
from app.web.config import Config


# @pytest.fixture(scope="session", autouse=True)
# def fake_vk():
#     # crashes after test method...
#     with aioresponses() as mock:
#         mock.get(
#             re.compile(r"^https://api\.vk\.com/method/groups\.getLongPollServer.+$"),
#             status=200,
#             payload={"response": {"key": "key",
#                                   "server": "https://vk_server.com",
#                                   "ts": "ts"}}
#         )
#         yield


@pytest.fixture(scope="session")
def loop():
    with loop_context() as _loop:
        yield _loop


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


@pytest.fixture(scope="session")
def server() -> Application:
    config_file = pathlib.Path(__file__).resolve().parent.parent / "test_config.yaml"
    _app = setup_app(config_file)
    return _app


@pytest.fixture
def app_config(server) -> Config:
    return server.config


@pytest.fixture
def cli(aiohttp_client, loop, server, chat_id) -> TestClient:
    client = loop.run_until_complete(aiohttp_client(server))
    yield client
    loop.run_until_complete(clear_db(server, chat_id))


@pytest.fixture
async def authed_cli(cli, app_config) -> TestClient:
    await cli.post(
        "/admin.login",
        data={
            "email": app_config.admin.email,
            "password": app_config.admin.password,
        },
    )
    yield cli


@pytest.fixture
def application(cli) -> Application:
    return cli.app


async def clear_db(server: Application, chat_id):
    db = server.database.db
    for table in db.sorted_tables:
        await db.status(db.text(f"TRUNCATE {table.name} CASCADE"))
        await db.status(db.text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH 1"))
    server.store.states.restore_status(chat_id)
