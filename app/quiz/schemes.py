from marshmallow import Schema, fields, validate

from app.web.schemes import OkResponseSchema


# ----------------------------------------------------


class ThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)


class AddThemeRequestSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1))


class AddThemeResponseSchema(OkResponseSchema):
    data = fields.Nested(ThemeSchema)


# ----------------------------------------------------

class ThemeListSchema(Schema):
    themes = fields.Nested(ThemeSchema, many=True)


class ThemeListResponseSchema(OkResponseSchema):
    data = fields.Nested(ThemeListSchema)


# ----------------------------------------------------


class AnswerSchema(Schema):
    title = fields.Str(required=True)
    is_correct = fields.Bool(required=True)
    description = fields.Str(required=False)


# ----------------------------------------------------


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    theme_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    answers = fields.Nested(AnswerSchema, required=True, many=True, validate=validate.Length(equal=4))


class AddQuestionRequestSchema(QuestionSchema):
    pass


class AddQuestionResponseSchema(OkResponseSchema):
    data = fields.Nested(QuestionSchema)


# ----------------------------------------------------


class QueryThemeIdSchema(Schema):
    theme_id = fields.Int(required=False)


class ListQuestionSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)


class ListQuestionResponseSchema(OkResponseSchema):
    data = fields.Nested(ListQuestionSchema)


# ----------------------------------------------------


class DeleteThemeRequestSchema(Schema):
    theme_id = fields.Int(required=True)


class DeleteThemeResponseSchema(OkResponseSchema):
    data = fields.Nested(ThemeSchema)


# ----------------------------------------------------


class DeleteQuestionRequestSchema(Schema):
    question_id = fields.Int(required=True)


class DeleteQuestionResponseSchema(OkResponseSchema):
    data = fields.Nested(QuestionSchema)
