
import os
from sqlalchemy import create_engine, text

database_url = os.getenv("Database_URL")

if not database_url:
    raise RuntimeError("Database_URL environment variable is missing")

engine = create_engine(database_url)

try:
    with engine.connect() as connection:
        print("Connected database:", connection.execute(
            text("SELECT current_database()")
        ).scalar())

        tables = connection.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)).scalars().all()

        print("Existing public tables:", tables)
finally:
    engine.dispose()
