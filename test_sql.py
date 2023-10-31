from tortoise import Tortoise, run_async
from app.models import Tournament
async def init():
    #  Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url='postgres://postgres:SQLsemen5656@localhost:5432/test',
        modules={'models': ['app.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()

# run_async is a helper function to run simple async Tortoise scripts.
if __name__ == "__main__":
    run_async(init())
