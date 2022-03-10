import asyncio

import pytest
from pytest_mock import MockerFixture

from app.store.vk_api import events
from app.store.vk_api.updates_poller import EventType


@pytest.fixture(autouse=True)
def cancel_tasks(application):
    yield
    for task in application.store.vk_updates_poller.tasks:
        task.cancel()
    application.store.vk_updates_poller.tasks.clear()


class TestVKUpdatesPoller:

    async def test_queue(self, application):
        application.store.vk_updates_poller.tasks.clear()
        await application.store.vk_updates_queue.put({})
        assert not application.store.vk_updates_queue.empty()

    async def test_queue_poller(self, application, mocker: MockerFixture):
        handle_update = mocker.patch.object(application.store.vk_updates_poller, "handle_update")
        update = {"type": EventType.message_new}
        await application.store.vk_updates_queue.put(update)
        while not application.store.vk_updates_queue.empty():
            await asyncio.sleep(0.1)
        handle_update.assert_called_once_with(update)

    async def test_handle_invite(self, application, mocker: MockerFixture):
        mock_object = mocker.patch.object(events, "ChatInviteRequest")
        update = {"type": EventType.message_new,
                  "object": {"message": {"action": {"type": EventType.chat_invite_user}}}}
        n_tasks = len(application.store.vk_updates_poller.tasks)
        await application.store.vk_updates_poller.handle_update(update)
        mock_object.assert_called_once()
        assert len(application.store.vk_updates_poller.tasks) == n_tasks + 1

    async def test_handle_message_text(self, application, mocker: MockerFixture):
        mock_object = mocker.patch.object(events, "MessageText")
        update = {"type": EventType.message_new,
                  "object": {"message": {}}}
        n_tasks = len(application.store.vk_updates_poller.tasks)
        await application.store.vk_updates_poller.handle_update(update)
        mock_object.assert_called_once()
        assert len(application.store.vk_updates_poller.tasks) == n_tasks + 1

    async def test_handle_message_callback(self, application, mocker: MockerFixture):
        mock_object = mocker.patch.object(events, "MessageCallback")
        update = {"type": EventType.message_event}
        n_tasks = len(application.store.vk_updates_poller.tasks)
        await application.store.vk_updates_poller.handle_update(update)
        mock_object.assert_called_once()
        assert len(application.store.vk_updates_poller.tasks) == n_tasks + 1

    async def test_garbage_collector(self, application):
        assert len(application.store.vk_updates_poller.tasks) == 1
        application.store.vk_updates_poller.tasks[0].cancel()
        await asyncio.sleep(0.5)
        assert len(application.store.vk_updates_poller.tasks) == 0
