from contextlib import asynccontextmanager
from tortoise import Tortoise
import asyncio
from models.Users import User
from models.Devices import Device
from models.Snapshots import Snapshot_WindDirection, Snapshot_WindSpeed, Snapshot_TempAir, Snapshot_TempSoil, Snapshot_HumAir, Snapshot_HumSoil, Snapshot_Rainfall, Snapshot_GPS, Snapshot_BatteryVoltage, Snapshot_Error


from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, conlist
from typing import Optional
from datetime import datetime, timedelta
import jwt
import secrets
import string
from typing import Optional

ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class Report(BaseModel):
    data: dict
    device_id: int
    
class DeviceObject(BaseModel):
    name: str
    description: str
    user_id: Optional[int]

class UserObject(BaseModel):
    name: str
    password: str
    role: str
    photo_url: Optional[str]

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, 'secret', algorithm='HS256')
    return encoded_jwt

@asynccontextmanager
async def lifespan(app: FastAPI):
    # выполняется при запуске
    
    await Tortoise.init(
        db_url='postgres://postgres:SQLsemen5656@localhost:5432/test',
        modules={'models': ['models.Users','models.Devices','models.Snapshots']}
    )
    await Tortoise.generate_schemas()
    
    ############################################################################
    yield
    # выполняется перед выключением
    await Tortoise.close_connections()

app = FastAPI(lifespan=lifespan)


# async def list_users():
#     users = await User.all()
#     count_users = await User.all().count()
#     print(f'Users count: {count_users}')
#     for user in users:
#         print(f"ID: {user.id} Name: {user.name} Password: {user.password} Role: {user.role} Photo: {user.photo_url}")
    
async def report_processing(report: Report):
    start_time = datetime.now()
    data = report.data
    air_data = report.data['air']
    soil_data = report.data['soil']
    
    device_id = report.device_id
    
    device = await Device.get(id=device_id)
    
    
    for i in range(len(data['gps']['date_time'])):
        
        date_time = datetime.strptime(data['gps']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_gps = Snapshot_GPS(device=device, date=date_time, latitude=data['gps']['latitude'][i], longitude=data['gps']['longitude'][i])
        await snapshot_gps.save()
    
    for i in range(len(data['rainfall']['date_time'])):
        date_time = datetime.strptime(data['rainfall']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_rainfall = Snapshot_Rainfall(device=device, date=date_time, rain=data['rainfall']['data'][i])
        await snapshot_rainfall.save()
        
    for i in range(len(data['battery_voltage']['date_time'])):
        date_time = datetime.strptime(data['battery_voltage']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_battery_voltage = Snapshot_BatteryVoltage(device=device, date=date_time, voltage=data['battery_voltage']['data'][i])
        await snapshot_battery_voltage.save()
    
    for i in range(len(air_data['temperature'])):
        date_time = datetime.strptime(air_data['temperature']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_temp_air = Snapshot_TempAir(device=device, date=date_time, temperature=air_data['temperature']['data'][i])
        await snapshot_temp_air.save()
    
    for i in range(len(air_data['humidity'])):
        date_time = datetime.strptime(air_data['humidity']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_hum_air = Snapshot_HumAir(device=device, date=date_time, humidity=air_data['humidity']['data'][i])
        await snapshot_hum_air.save()
    
    for i in range(len(soil_data['temperature'])):
        date_time = datetime.strptime(soil_data['temperature']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_temp_soil = Snapshot_TempSoil(device=device, date=date_time, temperature=soil_data['temperature']['data'][i])
        await snapshot_temp_soil.save()
    
    for i in range(len(soil_data['humidity'])):
        date_time = datetime.strptime(soil_data['humidity']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_hum_soil = Snapshot_HumSoil(device=device, date=date_time, humidity=soil_data['humidity']['data'][i])
        await snapshot_hum_soil.save()
    
    for i in range(len(air_data['wind_speed']['date_time'])):
        date_time = datetime.strptime(air_data['wind_speed']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_wind_speed = Snapshot_WindSpeed(device=device, date=date_time, wind_speed=air_data['wind_speed']['data'][i])
        await snapshot_wind_speed.save()
    
    for i in range(len(air_data['wind_direction']['date_time'])):
        date_time = datetime.strptime(air_data['wind_direction']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_wind_direction = Snapshot_WindDirection(device=device, date=date_time, wind_direction=air_data['wind_direction']['data'][i])
        await snapshot_wind_direction.save()
    
    for i in range(len(data['errors']['date_time'])):
        date_time = datetime.strptime(data['errors']['date_time'][i], "%d.%m.%Y,%H:%M:%S")
        snapshot_error = Snapshot_Error(device=device, date=date_time, error_message=data['errors']['data'][i])
        await snapshot_error.save()
    
    finish_time = datetime.now()
    print(f"Report processing time: {finish_time - start_time}")
    
@app.post('/report')
async def report(report: Report, background_tasks: BackgroundTasks):
    
    background_tasks.add_task(report_processing, report)
    
    return {'status' : 'received'}

@app.post('/add_device')
async def add_device(device: DeviceObject):
    print
    if device.user_id != None:
        user = await User.get(id=device.user_id)
        new_device = Device(name=device.name, description=device.description, user=user)
    else:
        new_device = Device(name=device.name, description=device.description)
    await new_device.save()
    return {'status' : 'succses'}

@app.post('/add_user')
async def add_user(user: UserObject):
    new_user = User(name=user.name, password=user.password, role=user.role, photo_url=user.photo_url)
    await new_user.save()
    return {'status' : 'succses'}

@app.post('/generate_token')
async def generate_token(email: str, password: str):
    user = await User.get(name=email)
    if user.password == password:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        return {'status' : 'wrong password'}

@app.get('/get_devices')
async def get_devices():
    devices = await Device.all()
    devices_list = []
    for device in devices:
        devices_list.append({'id' : device.id, 'name' : device.name, 'description' : device.description, 'user_id' : device.user.id, 'registration_date' : device.registration_date})
    return {'devices' : devices_list}

@app.get('/get_device_by_id')
async def get_device_by_id(device_id: int):
    device = await Device.get(id=device_id)
    
    if device:
    
        device_data = {
            'id': device.id,
            'name': device.name,
            'description': device.description,
            'user_id': None,  # По умолчанию устанавливаем user_id как None
            'registration_date': device.registration_date,
        }
        
        if device.user:
            device_data['user_id'] = device.user.id
        
        return {'status' : 'success', 'data' : device_data}
    else:
        return {'status' : 'error', 'message' : 'device does not exist'}

@app.get('/get_devices_by_user_id')
async def get_devices_by_user_id(user_id: int):
    user = await User.get(id=user_id)
    if user:
        devices = await Device.filter(user=user)
        if devices:
            devices_list = []
            for device in devices:
                devices_list.append({'id' : device.id, 'name' : device.name, 'description' : device.description, 'user_id' : device.user.id, 'registration_date' : device.registration_date})
            return {'status' : 'success' ,'data' : devices_list}
        else:
            return {'status' : 'error', 'message' : 'user does not have devices'}
    else:
        return {'status' : 'error', 'message' : 'user does not exist'}
    

@app.get('/get_devices_by_username')
async def get_devices_by_username(username: str):
    user = await User.get(name=username)
    if user:
        devices = await Device.filter(user=user)
        devices_list = []
        if devices:
            for device in devices:
                devices_list.append({'id' : device.id, 'name' : device.name, 'description' : device.description, 'user_id' : device.user.id, 'registration_date' : device.registration_date})
            return {'status' : 'success', 'data' : devices_list}
        else:
            return {'status' : 'error', 'message' : 'user does not have devices'}
    else:
        return {'status' : 'error', 'message' : 'user does not exist'}

@app.post('/check_device_existance')
async def check_device_existance(device_id: int):
    device = await Device.get(id=device_id)
    if device:
        return {'status' : 'success', 'message' : 'device exists'}
    else:
        return {'status' : 'success', 'message' : 'device does not exist'}

@app.post('/check_user_existance')
async def check_user_existance(username: str):
    user = await User.get(name=username)
    if user:
        return {'status' : 'error', 'message' : 'user exists'}
    else:
        return {'status' : 'error', 'message' : 'user does not exist'}

@app.post('/set_user_for_device')
async def set_user_for_device(device_id: int, user_id: int):
    device = await Device.get(id=device_id)
    user = await User.get(id=user_id)
    if device and user:
        device.user = user
        await device.save()
        return {'status' : 'success', 'message' : 'user set for device'}
    else:
        return {'status' : 'error', 'message' : 'user or device does not exist'}

@app.post('/delete_user_for_device')
async def delete_user_for_device(device_id: int):
    device = await Device.get(id=device_id)
    if device:
        device.user = None
        await device.save()
        return {'status' : 'success', 'message' : 'user deleted for device'}
    else:
        return {'status' : 'error', 'message' : 'device does not exist'}

@app.post('/delete_user')
async def delete_user(user_id: int):
    user = await User.get(id=user_id)
    if user:
        await user.delete()
        return {'status' : 'success', 'message' : 'user deleted'}
    else:
        return {'status' : 'error', 'message' : 'user does not exist'}

@app.get('/get_snapshots')
async def get_snapshots(device_id: int, start_date: datetime, end_date: datetime, type: str):
    if device_id and start_date and end_date and type:
        device = await Device.get(id=device_id)
        if device:
            if type == 'gps':
                snapshots = await Snapshot_GPS.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'latitude' : snapshot.latitude, 'longitude' : snapshot.longitude})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'rainfall':
                snapshots = await Snapshot_Rainfall.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'rain' : snapshot.rain})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'battery_voltage':
                snapshots = await Snapshot_BatteryVoltage.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'voltage' : snapshot.voltage})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'temp_air':
                snapshots = await Snapshot_TempAir.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'temperature' : snapshot.temperature})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'hum_air':
                snapshots = await Snapshot_HumAir.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'humidity' : snapshot.humidity})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'temp_soil':
                snapshots = await Snapshot_TempSoil.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'temperature' : snapshot.temperature})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'hum_soil':
                snapshots = await Snapshot_HumSoil.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'humidity' : snapshot.humidity})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'wind_speed':
                snapshots = await Snapshot_WindSpeed.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'wind_speed' : snapshot.wind_speed})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'wind_direction':
                snapshots = await Snapshot_WindDirection.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'wind_direction' : snapshot.wind_direction})
                return {'status' : 'success', 'data' : snapshots_list}
            elif type == 'error':
                snapshots = await Snapshot_Error.filter(device=device, date__gte=start_date, date__lte=end_date)
                snapshots_list = []
                for snapshot in snapshots:
                    snapshots_list.append({'id' : snapshot.id, 'date' : snapshot.date, 'error_message' : snapshot.error_message})
                return {'status' : 'success', 'data' : snapshots_list}
            else:
                return {'status' : 'error', 'message' : 'wrong type'}

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)