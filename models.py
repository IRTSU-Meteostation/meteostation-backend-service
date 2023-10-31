from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50)
    email = fields.CharField(max_length=100)
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.username