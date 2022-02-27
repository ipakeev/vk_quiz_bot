from typing import Any, Optional
from typing import Type

from aiohttp.abc import AbstractView
from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_response import Response

HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


def json_response(data: Any = None, status: str = "ok") -> Response:
    if data is None:
        data = {}
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
        status_code: int,
        message: Optional[str] = None,
        data: Optional[dict] = None,
):
    res = aiohttp_json_response(
        data={
            "status": HTTP_ERROR_CODES[status_code],
            "message": message,
            "data": data,
        },
        status=status_code,
    )
    return res


def require_login(func: Type[AbstractView]) -> Type[AbstractView]:
    func.__require_login__ = True
    return func
