from django.conf import settings
import hashlib
import uuid


def md5(string):
    hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_object.update(string.encode('utf-8'))
    return hash_object.hexdigest()


def uid(string):
    data = f'{uuid.uuid4()}-{string}'
    return md5(data)
