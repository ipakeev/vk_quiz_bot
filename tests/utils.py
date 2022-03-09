from typing import Union

from app.web.app import Application


def ok_response(data: Union[list, dict]):
    return {
        "status": "ok",
        "data": data,
    }


def error_response(status: str, message: str, data: dict):
    return {
        "status": status,
        "message": message,
        "data": data,
    }


async def check_empty_table_exists(application: Application, tablename: str):
    db = application.database.db
    query = db.text(f"SELECT count(1) FROM {tablename}")
    count = await db.scalar(query)
    assert count == 0
