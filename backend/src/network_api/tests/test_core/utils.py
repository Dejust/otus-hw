from pydantic import SecretStr

from network_api.core.users.models import Profile, Name, Age, City, Interests, Gender, Credentials
from network_api.tests.utils import faker


def build_profile():
    return Profile(
        first_name=Name(faker.first_name()),
        last_name=Name(faker.last_name()),

        age=Age(faker.pyint(min_value=5, max_value=30)),
        city=City(faker.city()),
        interests=Interests(faker.text()),
        gender=Gender('m')
    )


def build_credentials():
    return Credentials(email=faker.email(), password=SecretStr(faker.password()))