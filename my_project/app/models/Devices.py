from tortoise.models import Model
from tortoise import fields


class Device(Model):
    id = fields.IntField(pk=True)
    registration_date = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=16, unique=True)
    description = fields.CharField(max_length=256, null=True)
    user = fields.ForeignKeyField('models.User', related_name='devices', null=True)
    