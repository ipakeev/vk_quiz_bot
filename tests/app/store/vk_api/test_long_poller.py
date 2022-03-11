import re

import pytest
from aioresponses import aioresponses
from pytest_mock import MockerFixture


@pytest.mark.skip()
class TestVKLongPoller:

    async def test_poll_service(self, application):
        pass

    async def test_query_long_poll(self, application, mocker: MockerFixture):
        queue_put = mocker.patch.object(application.store.vk_updates_queue, "put")
        poll_service = mocker.patch.object(application.store.vk_long_poller, "init_long_poll_service")
        with aioresponses() as mock:
            mock.get(
                re.compile(r"^https://vk_server\.com.+$"),
                status=200,
                payload={"ts": "ts"},
            )
            await application.store.vk_long_poller.query_long_poll()
            queue_put.assert_not_called()
            poll_service.assert_not_called()

        with aioresponses() as mock:
            mock.get(
                re.compile(r"^https://vk_server\.com.+$"),
                status=200,
                payload={"ts": "ts", "updates": [{}]},
            )
            await application.store.vk_long_poller.query_long_poll()
            queue_put.assert_called_once()
            poll_service.assert_not_called()

        with aioresponses() as mock:
            mock.get(
                re.compile(r"^https://vk_server\.com.+$"),
                status=200,
                payload={"fail": "foo"},
            )
            await application.store.vk_long_poller.query_long_poll()
            queue_put.assert_not_called()
            poll_service.assert_called_once()
