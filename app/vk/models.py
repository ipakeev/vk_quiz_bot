from dataclasses import dataclass

from app.base.database import db
from app.utils import now


# import typing
# if typing.TYPE_CHECKING:
#     import sqlalchemy as db


@dataclass
class UserDC:
    id: int  # this is vk_id
    first_name: str
    last_name: str

    def as_model(self) -> "UserModel":
        return UserModel(id=self.id, first_name=self.first_name, last_name=self.last_name)


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    joined_at = db.Column(db.DateTime(), default=now)


@dataclass
class ChatDC:
    id: int  # this is vk_id

    def as_model(self) -> "ChatModel":
        return ChatModel(id=self.id)


class ChatModel(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)  # this is vk_id
    joined_at = db.Column(db.DateTime(), default=now)
