from dataclasses import dataclass

from app.base.database import db
from app.utils import encode_password


# import typing
# if typing.TYPE_CHECKING:
#     import sqlalchemy as db


@dataclass
class AdminDC:
    id: int
    email: str
    password: str

    def is_correct_password(self, password: str) -> bool:
        return encode_password(password) == self.password


class AdminModel(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    def as_dataclass(self) -> AdminDC:
        return AdminDC(id=self.id, email=self.email, password=self.password)
