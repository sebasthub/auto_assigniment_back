from tortoise import fields
from tortoise.models import Model


class RefreshToken(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens")
    jti = fields.CharField(max_length=64, unique=True, index=True)
    token_hash = fields.CharField(max_length=64, unique=True, index=True)
    token_family = fields.CharField(max_length=64, index=True)
    revoked_at = fields.DatetimeField(null=True)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    replaced_by_jti = fields.CharField(max_length=64, null=True)
    user_agent = fields.CharField(max_length=512, null=True)
    ip_address = fields.CharField(max_length=64, null=True)
