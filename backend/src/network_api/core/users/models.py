import re
from typing import Any

import bcrypt

from pydantic import BaseModel, EmailStr, SecretStr, StrictStr, StrictInt, PrivateAttr


class Credentials(BaseModel):
    email: EmailStr
    password: SecretStr


class HashedCredentials(BaseModel):
    email: EmailStr
    password_hash: str

    @classmethod
    def create_from(cls, credentials: Credentials):
        password_hash = bcrypt.hashpw(
            credentials.password.get_secret_value().encode('utf8'), bcrypt.gensalt()
        ).decode('utf8')

        # noinspection PyArgumentList
        return cls(
            email=credentials.email,
            password_hash=password_hash
        )

    def check_password_valid(self, password: SecretStr):
        return bcrypt.checkpw(password.get_secret_value().encode('utf8'), self.password_hash.encode('utf8'))


class Name(StrictStr):
    min_length = 1
    max_length = 255


class Age(StrictInt):
    gt = 0
    lt = 100


class City(StrictStr):
    min_length = 1
    max_length = 255


class Interests(StrictStr):
    max_length = 512


class Gender(StrictStr):
    regex = re.compile('^f|m$')


class Profile(BaseModel):
    first_name: Name
    last_name: Name

    age: Age
    city: City
    interests: Interests
    gender: Gender


class User(BaseModel):
    id: StrictInt = None

    profile: Profile = None
    credentials: HashedCredentials = None

    def add_credentials(self, credentials: Credentials) -> HashedCredentials:
        self.credentials = HashedCredentials.create_from(credentials)
        return self.credentials
