import typing
from typing import Optional

from sqlalchemy.dialects.postgresql import insert

from app.admin.models import AdminDC, AdminModel
from app.base.accessor import BaseAccessor
from app.utils import encode_password

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):

    async def connect(self, app: "Application"):
        await self.create_admin(email=app.config.admin.email, password=app.config.admin.password)

    async def get_by_email(self, email: str) -> Optional[AdminDC]:
        admin_model: AdminModel = await AdminModel.query.where(AdminModel.email == email).gino.first()
        if admin_model:
            return admin_model.as_dataclass()

    async def create_admin(self, email: str, password: str):
        password = encode_password(password)
        query = insert(AdminModel).values(email=email, password=password).on_conflict_do_nothing()
        await query.gino.status()
