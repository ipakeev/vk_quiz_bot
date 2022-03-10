import asyncio
from app.utils import generate_uuid


class TestVKBot:

    async def test_garbage_collector(self, application):
        assert len(application.store.vk_bot.tasks) == 0

        async def task(seconds: float):
            await asyncio.sleep(seconds)

        uid = generate_uuid()
        await application.store.vk_bot.schedule_task(uid, task(10.0))
        await asyncio.sleep(0.5)
        assert len(application.store.vk_bot.tasks) == 1

        await application.store.vk_bot.cancel_task(uid)
        await asyncio.sleep(0.5)
        assert len(application.store.vk_bot.tasks) == 0

        await application.store.vk_bot.schedule_task(uid, task(0.1))
        assert len(application.store.vk_bot.tasks) == 1
        await asyncio.sleep(0.5)
        assert len(application.store.vk_bot.tasks) == 0
