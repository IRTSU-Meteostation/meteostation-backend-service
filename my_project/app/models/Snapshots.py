from tortoise.models import Model
from tortoise import fields

class Snapshot_WindDirection(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_wd')
    date = fields.DatetimeField(auto_now_add=True)
    
    wind_direction = fields.FloatField(null=True)
    
class Snapshot_WindSpeed(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_ws')
    date = fields.DatetimeField(auto_now_add=True)
    
    wind_speed = fields.FloatField(null=True)
    
class Snapshot_TempAir(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_ta')
    date = fields.DatetimeField(auto_now_add=True)
    
    temperature = fields.FloatField(null=True)
    
class Snapshot_TempSoil(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_ts')
    date = fields.DatetimeField(auto_now_add=True)
    
    temperature = fields.FloatField(null=True)
    
class Snapshot_HumAir(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_ha')
    date = fields.DatetimeField(auto_now_add=True)
    
    humidity = fields.FloatField(null=True)
    
class Snapshot_HumSoil(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_hs')
    date = fields.DatetimeField(auto_now_add=True)
    
    humidity = fields.FloatField(null=True)


class Snapshot_Rainfall(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_r')
    date = fields.DatetimeField(auto_now_add=True)
    
    rain = fields.FloatField(null=True)
    
class Snapshot_GPS(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_gps')
    date = fields.DatetimeField(auto_now_add=True)
    
    latitude = fields.FloatField(null=True)
    longitude = fields.FloatField(null=True)

    
class Snapshot_BatteryVoltage(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='snapshots_bv')
    date = fields.DatetimeField(auto_now_add=True)
    
    voltage = fields.FloatField(null=True)
    
    

class Snapshot_Error(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='errors')
    date = fields.DatetimeField(auto_now_add=True)
    
    #error_type = fields.CharField(max_length=64, null=True)
    
    error_message = fields.CharField(max_length=256, null=True)
    
    #error_code = fields.IntField(null=True)
    
    #error_description = fields.CharField(max_length=256, null=True)