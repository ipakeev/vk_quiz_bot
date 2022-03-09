class TestAdminAccessor:

    async def test_create_on_startup(self, application, app_config):
        admin = await application.store.admins.get_by_email(app_config.admin.email)
        assert admin is not None
        assert admin.email == app_config.admin.email
        # Password must be hashed
        assert admin.password != app_config.admin.password
        assert admin.id == 1

    async def test_not_existed_email(self, application):
        admin = await application.store.admins.get_by_email("not_existed@admin.ru")
        assert admin is None
