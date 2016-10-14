from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.constants import STRING, STRING_SET
from pynamodb.models import Model


class Relationship(Attribute):
    def __init__(self, model, hash_key="id", **args):
        if not issubclass(model, Model):
            raise TypeError("Expected PynamoDB Model argument, got: %s " % model.__class__.__name__)

        Attribute.__init__(self, **args)
        self.model = model
        self.hash_key = hash_key


class OneToOne(Relationship):
    attr_type = STRING

    def serialize(self, model):
        return getattr(model, self.hash_key)

    def deserialize(self, hash_key):
        if isinstance(getattr(self.model, self.hash_key)):
            hash_key = int(hash_key)

        try:
            return self.model.get(hash_key)
        except self.model.DoesNotExist:
            return None


class OneToMany(Relationship):
    attr_type = STRING_SET

    def serialize(self, models):
        return [getattr(model, self.key_name) for model in models]

    def deserialize(self, hash_keys):
        if isinstance(getattr(self.model, self.key_name), NumberAttribute):
            hash_keys = map(int, hash_keys)

        try:
            return self.model.batch_get(hash_keys)
        except self.model.DoesNotExist:
            return None
