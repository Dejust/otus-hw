import aiomysql

from . import config


async def create_pool() -> aiomysql.Pool:
    pool = await aiomysql.create_pool(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        db=config.DB_NAME,
        autocommit=True
    )

    return pool


async def create_tables(db_cursor: aiomysql.Cursor, *, reset=False):
    if reset:
        await drop_tables(db_cursor)

    await db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            first_name VARCHAR(255) NULL,
            last_name VARCHAR(255) NULL,
            email VARCHAR(255) NULL UNIQUE,
            password_hash VARCHAR(255) NULL,
            age INTEGER NULL CHECK (age > 0),
            city VARCHAR(255) NULL,
            interests VARCHAR(512) NULL,
            gender ENUM('m', 'f') NULL
        );
        
        CREATE TABLE IF NOT EXISTS friends (
            source_user_id INTEGER NOT NULL,
            target_user_id INTEGER NOT NULL,
            FOREIGN KEY (source_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (source_user_id, target_user_id)
        )
    """)


async def drop_tables(db_cursor: aiomysql.Cursor):
    await db_cursor.execute("""
        DROP TABLE IF EXISTS friends;
        DROP TABLE IF EXISTS users;
    """)
