import asyncio
from database import engine
from models import Base

async def main():
    async with engine.begin() as conn:
        print('Dropping all tables...')
        await conn.run_sync(Base.metadata.drop_all)
    print('Done.')

asyncio.run(main())
