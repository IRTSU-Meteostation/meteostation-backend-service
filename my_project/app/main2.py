from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from tortoise.models import Model
from tortoise import fields, Tortoise
from typing import Optional
from datetime import datetime, timedelta
import jwt
import secrets
import string
import bcrypt
from typing import List


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Время окна для разрешенного обновления токена после истечения срока действия (в минутах)
REFRESH_WINDOW_MINUTES = 15

# # Максимальное количество разрешенных обновлений токена
MAX_REFRESH_COUNT = 3


# Модель для токена
class Token(BaseModel):
    access_token: str
    token_type: str
    

class UserRegistration(BaseModel):
    username: str
    password: str
    
class UserPublic(BaseModel):
    id: int
    username: str

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=16, unique=True)
    hashed_password = fields.CharField(max_length=60)

    class PydanticMeta:
        exclude = ["hashed_password"]  # Не возвращаем хэшированный пароль в ответах

# Создание токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def refresh_access_token(username: str, refresh_count: int):
    # Проверяем, не превысило ли количество обновлений максимальное значение
    if refresh_count >= MAX_REFRESH_COUNT:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh limit exceeded",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = create_access_token(data={"sub": username, "refresh_count": refresh_count + 1}, expires_delta=access_token_expires)
    return new_token
# Подключение Tortoise к FastAPI
app = FastAPI()



@app.on_event("startup")
async def startup_event():
    await Tortoise.init(
        db_url='postgres://postgres:SQLsemen5656@localhost:5432/test',
        modules={'models': ["__main__"]} #['models.user1']
    )
    await Tortoise.generate_schemas()

@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()

# Продолжение кода как раньше

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())



@app.get("/users", response_model=List[UserPublic])
async def get_users():
    users = await User.all().values('id', 'username')
    return users



@app.post("/reg_user")
async def register_user(user_data: UserRegistration):
    # Проверяем, существует ли уже пользователь с таким именем
    if await User.get_or_none(username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Хэшируем пароль
    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())

    # Создаем нового пользователя
    new_user = User(username=user_data.username, hashed_password=hashed_password.decode())
    await new_user.save()

    return {"message": "User registered successfully"}


# Аутентификация пользователя
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.get_or_none(username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, 
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user_and_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        refresh_allowed = now < exp_time + timedelta(minutes=REFRESH_WINDOW_MINUTES)
        if exp_time < now and refresh_allowed:
            # Если токен истек и разрешено обновление
            new_token = refresh_access_token(username, payload.get("refresh_count", 0))
            return {"user": await User.get_or_none(username=username), "token": new_token}
        user = await User.get_or_none(username=username)

        if user is None:
            raise credentials_exception
        return {"user": user, "token": token}
    except jwt.PyJWTError:
        raise credentials_exception

@app.get("/users/me")
async def read_users_me(data: dict = Depends(get_current_user_and_token)):
    user = data["user"]
    return {"user": {"id": user.id, "username": user.username}}

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
