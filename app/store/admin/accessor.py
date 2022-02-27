import typing
from typing import Optional

from app.admin.models import AdminDC, AdminModel
from app.database.accessor import BaseAccessor
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
        admin_model: AdminModel = await AdminModel.query.where(AdminModel.email == email).gino.first()
        if admin_model:
            self.app.logger.warning(f"admin {email} already exists")
        else:
            await AdminModel.create(email=email, password=encode_password(password))
            self.app.logger.info(f"created admin {email}")
