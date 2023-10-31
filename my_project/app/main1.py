from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from models.user1 import User
from tortoise import Tortoise
import asyncio


app = FastAPI()

@app.get("/users")
async def get_users():
    users = await User.all().values()
    return users

@app.post("/add_user")
async def add_user():
    new_user = User(
        # fill in the fields according to your User model
        username="John_Doe",
        password="johndoe@example.com",
        # ... other fields ...
    )
    await new_user.save()

    

@app.on_event("startup")
async def startup_event():
    await Tortoise.init(
        db_url='postgres://postgres:SQLsemen5656@localhost:5432/test',
        modules={'models': ['models.user1']}
    )
    await Tortoise.generate_schemas()

@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
