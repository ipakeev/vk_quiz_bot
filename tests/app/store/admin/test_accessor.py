class TestAdminAccessor:

    async def test_create_on_startup(self, store, config):
        admin = await store.admins.get_by_email(config.admin.email)
        assert admin is not None
        assert admin.email == config.admin.email
        # Password must be hashed
        assert admin.password != config.admin.password
        assert admin.id == 1

    async def test_not_existed_email(self, store):
        admin = await store.admins.get_by_email("not_existed@admin.ru")
        assert admin is None
