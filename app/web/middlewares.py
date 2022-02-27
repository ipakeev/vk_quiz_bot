import json
import typing

import aiohttp_session
import marshmallow
from aiohttp import web
from aiohttp import web_exceptions
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import cookie_storage
from aiohttp_session import session_middleware

from app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
        return response
    except web_exceptions.HTTPUnprocessableEntity as e:
        return error_json_response(
            status_code=400,
            message=e.reason,
            data=json.loads(e.text),
        )
    except marshmallow.ValidationError as e:
        return error_json_response(
            status_code=400,
            data=e.messages,
        )
    except json.JSONDecodeError as e:
        return error_json_response(
            status_code=400,
            message=e.msg,
        )
    except web_exceptions.HTTPUnauthorized as e:
        return error_json_response(
            status_code=401,
            message=e.text,
        )
    except web_exceptions.HTTPForbidden as e:
        return error_json_response(
            status_code=403,
            message=e.text,
        )
    except cookie_storage.InvalidToken as e:
        return error_json_response(
            status_code=403,
            message='Invalid cookies.',
        )
    except web_exceptions.HTTPNotFound as e:
        return error_json_response(
            status_code=404,
            message=e.text,
        )
    except web_exceptions.HTTPNotImplemented as e:
        return error_json_response(
            status_code=405,
            message=e.text,
        )
    except web_exceptions.HTTPConflict as e:
        return error_json_response(
            status_code=409,
            message=e.text,
        )


@web.middleware
async def check_login(request: "Request", handler) -> web.StreamResponse:
    require_login = getattr(handler, "__require_login__", False)
    if require_login:
        session = await aiohttp_session.get_session(request)
        admin_email = session.get('admin_email')

        if admin_email is None:
            if request.cookies:
                raise cookie_storage.InvalidToken()
            else:
                raise web_exceptions.HTTPUnauthorized(text='You must first log in.')
    return await handler(request)


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(session_middleware(
        cookie_storage.EncryptedCookieStorage(app.config.web_session.key)
    ))
    app.middlewares.append(check_login)
    app.middlewares.append(validation_middleware)
