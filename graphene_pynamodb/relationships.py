from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.constants import STRING, STRING_SET
from pynamodb.models import Model


class Relationship(Attribute):
    def __init__(self, model, key_name="id", **args):
        if not issubclass(model, Model):
            raise TypeError("Expected PynamoDB Model argument, got: %s " % model.__class__.__name__)

        Attribute.__init__(self, **args)
        self.model = model
        self.key_name = key_name


class OneToOne(Relationship):
    attr_type = STRING

    def serialize(self, value):
        return getattr(value, self.key_name)

    def deserialize(self, value):
        if isinstance(getattr(self.model, self.key_name), NumberAttribute):
            return self.model.get(int(value))
        else:
            return self.model.get(value)


class OneToMany(Relationship):
    attr_type = STRING_SET

    def serialize(self, models):
        return [getattr(model, self.key_name) for model in models]

    def deserialize(self, values):
        if isinstance(getattr(self.model, self.key_name), NumberAttribute):
            return self.model.batch_get(map(int, values))
        else:
            return self.model.batch_get(values)
