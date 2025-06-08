import asyncpg
from miles.config import get_settings

async def get_conn():
    st = get_settings()
    return await asyncpg.connect(st.database_url)  # add `database_url` to Settings