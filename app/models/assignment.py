from tortoise import fields
from tortoise.models import Model


class Assignment(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    active = fields.BooleanField(default=True)
    deleted = fields.BooleanField(default=False)
    user = fields.ForeignKeyField("models.User", related_name="assignments")
