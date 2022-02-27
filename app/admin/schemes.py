from marshmallow import Schema, fields, validate

from app.web.schemes import OkResponseSchema


class AdminSchema(Schema):
    id = fields.Int(required=True)
    email = fields.Str(required=True)


class AdminLoginRequestSchema(Schema):
    email = fields.Str(required=True, validate=validate.Email())
    password = fields.Str(required=True, validate=validate.Length(min=1))


class AdminLoginResponseSchema(OkResponseSchema):
    data = fields.Nested(AdminSchema)


# -----------------------------------------------

class AdminCurrentViewResponseSchema(AdminLoginResponseSchema):
    pass
