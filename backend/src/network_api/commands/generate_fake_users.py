import asyncio
import random

from faker import Faker

from network_api.database import create_pool

faker = Faker()

BATCH_NUMBER = 100
ROWS_NUMBER = 10000


def generate_email(batch_idx, row_idx):
    email = faker.email()
    return f'{batch_idx}-{row_idx}-{email}'


async def generate_fake_users(cursor):
    batch = [('first_name', 'last_name', 'foo@example.com', 10, 'MSK', '', 'f', '')] * ROWS_NUMBER
    genders = ['f', 'm']
    for batch_idx in range(BATCH_NUMBER):
        print('generate')
        for row_idx in range(ROWS_NUMBER):
            batch[row_idx] = (
                faker.first_name(),
                faker.last_name(),
                generate_email(batch_idx, row_idx),
                faker.pyint(1, 10),
                faker.city(),
                '',
                random.choice(genders),
                ''
            )

        print('execute')
        q = 'INSERT INTO users (first_name, last_name, email, age, city, interests, gender, password_hash) ' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'

        await cursor.executemany(q, batch)
        print(batch_idx, '/', BATCH_NUMBER)


async def main():
    db_pool = await create_pool()
    async with db_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await generate_fake_users(cursor)


if __name__ == '__main__':
    asyncio.run(main())
