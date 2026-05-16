from tortoise import fields
from tortoise.models import Model


class DocumentRecord(Model):
    uuid = fields.UUIDField(primary_key=True)
    original_name = fields.CharField(max_length=255)
    filename = fields.CharField(max_length=255)
    key = fields.CharField(max_length=255, unique=True, db_index=True)
    assignment = fields.OneToOneField("models.Assignment", related_name="document_record")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted = fields.BooleanField(default=False)

    @property
    def id(self):
        return self.uuid
