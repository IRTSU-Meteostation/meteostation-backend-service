from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    role = fields.CharField(max_length=16, default='user')
    name = fields.CharField(max_length=16, unique=True)
    password = fields.CharField(max_length=64)
    registration_date = fields.DatetimeField(auto_now_add=True)
    photo_url = fields.CharField(max_length=256, null=True)
    email = fields.CharField(max_length=256, null=True)