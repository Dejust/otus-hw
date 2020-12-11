import datetime

import jwt

from network_api.config import JWT_SECRET_KEY


def create(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, JWT_SECRET_KEY, algorithm='HS256')


def decode(token):
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
