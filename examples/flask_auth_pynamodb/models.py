import uuid

from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import AllProjection
from pynamodb.indexes import GlobalSecondaryIndex
from pynamodb.models import Model
from werkzeug.security import check_password_hash, generate_password_hash


def is_password_hash(pwhash):
    if pwhash.count('$') < 2:
        return False
    method, salt, hashval = pwhash.split('$', 2)

    return method.startswith('pbkdf2:') and len(method[7:].split(':')) in (1, 2)


class PasswordAttribute(UnicodeAttribute):
    def serialize(self, value):
        if is_password_hash(value):
            return value
        return generate_password_hash(value)

    def deserialize(self, value):
        return value


class UserEmailIndex(GlobalSecondaryIndex):
    class Meta:
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    email = UnicodeAttribute(hash_key=True)


class User(Model):
    class Meta:
        table_name = "users"
        host = "http://localhost:8000"

    def __init__(self, hash_key=None, range_key=None, **args):
        Model.__init__(self, hash_key, range_key, **args)
        if not self.id:
            self.id = str(uuid.uuid4())

    id = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute(null=False)
    email_index = UserEmailIndex()
    first_name = UnicodeAttribute(null=False)
    last_name = UnicodeAttribute(null=False)
    password = PasswordAttribute(null=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)


if not User.exists():
    User.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
