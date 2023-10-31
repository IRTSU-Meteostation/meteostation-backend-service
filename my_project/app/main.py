from tortoise import Tortoise
import asyncio
from models.user import User

async def init():
    await Tortoise.init(
        db_url='postgres://postgres:SQLsemen5656@localhost:5432/test',
        modules={'models': ['models.user']}
    )
    await Tortoise.generate_schemas()
    
async def list_users():
    users = await User.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")


async def run():
    await init()
    await list_users()


if __name__ == "__main__":
    asyncio.run(run())