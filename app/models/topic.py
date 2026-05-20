from tortoise import fields
from tortoise.models import Model


class Topic(Model):
    id = fields.IntField(pk=True)
    question = fields.TextField()
    response = fields.TextField(null=True)
    validated_response = fields.TextField(null=True)
    active = fields.BooleanField(default=True)
    deleted = fields.BooleanField(default=False)
    assignment = fields.ForeignKeyField("models.Assignment", related_name="topics")
