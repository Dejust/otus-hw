from starlette.config import Config

config = Config()

DB_HOST = config('DB_HOST', cast=str)
DB_PORT = config('DB_PORT', cast=int)
DB_USER = config('DB_USER', cast=str)
DB_PASSWORD = config('DB_PASSWORD', cast=str)
DB_NAME = config('DB_NAME', cast=str)

RO_DB_HOST = config('RO_DB_HOST', cast=str)
RO_DB_PORT = config('RO_DB_PORT', cast=int)
RO_DB_USER = config('RO_DB_USER', cast=str)
RO_DB_PASSWORD = config('RO_DB_PASSWORD', cast=str)
RO_DB_NAME = config('RO_DB_NAME', cast=str)

JWT_SECRET_KEY = config('JWT_SECRET_KEY', cast=str, default='123456')
