from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
import secrets
import string


# Конфигурация
SECRET_KEY = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Время окна для разрешенного обновления токена после истечения срока действия (в минутах)
REFRESH_WINDOW_MINUTES = 15

# # Максимальное количество разрешенных обновлений токена
MAX_REFRESH_COUNT = 3

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Модель пользователя для примера 
fake_users_db = {
    "johndoe": {                    #часто использую что то вроде этого
        "username": "johndoe",
        "hashed_password": "fakehashedsecret",
    }
}

# Модель для токена
class Token(BaseModel):
    access_token: str
    token_type: str

    
# Функция для обновления токена
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

# Аутентификация пользователя
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["hashed_password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, 
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

    # data = {
    #     'password' : 'fakehashedsecret', # пароль передаётся зашифрованным
    #     'username' : 'johndoe'
    # }
    # response = httpx.post(url + '/token', data=data)
    
    #{'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNjk4NDk5NTY0fQ.spJqXAd3dgo6TZb8JT_h-fb_uPrXhiA_aXUn4twytGE',
    #'token_type': 'bearer'}

# Функция для получения текущего пользователя и обновления токена
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
            return {"user": fake_users_db.get(username), "token": new_token}
        user = fake_users_db.get(username)
        if user is None:
            raise credentials_exception
        return {"user": user, "token": token}
    except jwt.PyJWTError:
        raise credentials_exception

# Защищенные эндпоинты
# (current_user: dict = Depends(get_current_user)) вот эта строчка за проверку токена и отвечает
# а точнее функция get_current_user
# токен передаём в headers = {"Authorization": f"Bearer {token}"}

# Защищенный эндпоинт
@app.get("/users/me")
async def read_users_me(data: dict = Depends(get_current_user_and_token)):
    user = data["user"]
    return {"user": user}



# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# @app.get("/time")
# async def get_current_time(current_user: dict = Depends(get_current_user_and_token)):
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     new_token = current_user["token"]
#     return {"current_time": current_time, "new_token": new_token}
