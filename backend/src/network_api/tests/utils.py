from faker import Faker

from network_api.core.users.models import User

faker = Faker()


def build_user():
    return User(id=faker.pyint())
