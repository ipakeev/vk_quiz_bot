from tests.utils import ok_response


class TestAdminLoginView:

    async def test_success_login(self, cli, app_config):
        resp = await cli.post(
            "/admin.login",
            json={
                "email": app_config.admin.email,
                "password": app_config.admin.password,
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            {
                "id": 1,
                "email": app_config.admin.email,
            }
        )

    async def test_authed_cli_success_login(self, authed_cli, app_config):
        await self.test_success_login(authed_cli, app_config)

    async def test_missed_email(self, cli):
        resp = await cli.post(
            "/admin.login",
            json={
                "password": "qwerty",
            },
        )
        assert resp.status == 400
        data = await resp.json()
        assert data["status"] == "bad_request"
        assert data["data"]["email"][0] == "Missing data for required field."

    async def test_not_valid_credentials(self, cli):
        resp = await cli.post(
            "/admin.login",
            json={
                "email": "qwerty@mail.ru",
                "password": "qwerty",
            },
        )
        assert resp.status == 403
        data = await resp.json()
        assert data["status"] == "forbidden"

    async def test_different_method(self, cli):
        resp = await cli.get(
            "/admin.login",
            json={
                "email": "qwerty",
                "password": "qwerty",
            },
        )
        assert resp.status == 405
        data = await resp.json()
        assert data["status"] == "not_implemented"


class TestAdminCurrentView:

    async def test_success(self, authed_cli, app_config):
        response = await authed_cli.get("/admin.current")
        assert response.status == 200

        data = await response.json()
        assert data == ok_response(dict(id=1, email=app_config.admin.email))

    async def test_unauthorized(self, cli):
        response = await cli.get("/admin.current")
        assert response.status == 401
