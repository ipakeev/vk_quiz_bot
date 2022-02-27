import aiohttp_session
from aiohttp import web_exceptions
from aiohttp_apispec import docs, request_schema, response_schema

from app.admin import schemes
from app.web.app import View
from app.web.utils import json_response, require_login


class AdminLoginView(View):
    @docs(description="Login method.")
    @request_schema(schemes.AdminLoginRequestSchema)
    @response_schema(schemes.AdminLoginResponseSchema)
    async def post(self):
        data = self.data

        # get credentials
        email = data["email"]
        password = data["password"]

        # verify it is admin and correct password
        admin = await self.store.admins.get_by_email(email)
        if not admin or not admin.is_correct_password(password):
            raise web_exceptions.HTTPForbidden(text="Email or password is wrong!")

        # create new session (set cookies) and bind with admin
        session = await aiohttp_session.new_session(self.request)
        session['admin_email'] = admin.email

        return json_response(
            data=schemes.AdminSchema().dump(admin),
        )

    async def get(self):
        raise web_exceptions.HTTPNotImplemented()


@require_login
class AdminCurrentView(View):
    @docs(description="Info about current admin.")
    @response_schema(schemes.AdminCurrentViewResponseSchema)
    async def get(self):
        session = await aiohttp_session.get_session(self.request)
        admin = await self.store.admins.get_by_email(session.get('admin_email'))
        return json_response(
            data=schemes.AdminSchema().dump(admin),
        )

    async def post(self):
        raise web_exceptions.HTTPNotImplemented()
