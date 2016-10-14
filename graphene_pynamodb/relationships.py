from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.constants import STRING, STRING_SET
from pynamodb.models import Model
from six import string_types


class Relationship(Attribute):
    _models = None

    @classmethod
    def sub_classes(cls, klass):
        return klass.__subclasses__() + [g for s in klass.__subclasses__() for g in Relationship.sub_classes(s)]

    @classmethod
    def get_model(cls, model_name):
        if not Relationship._models:
            Relationship._models = Relationship.sub_classes(Model)
        return next((model for model in Relationship._models if model.__name__ == model_name), None)

    def __init__(self, model, hash_key="id", **args):
        if not isinstance(model, string_types) and not issubclass(model, Model):
            raise TypeError("Expected PynamoDB Model argument, got: %s " % model.__class__.__name__)

        Attribute.__init__(self, **args)
        self._model = model
        self.hash_key = hash_key

    @property
    def model(self):
        if isinstance(self._model, string_types):
            self._model = Relationship.get_model(self._model)

        return self._model


class OneToOne(Relationship):
    attr_type = STRING

    def serialize(self, model):
        return getattr(model, self.hash_key)

    def deserialize(self, hash_key):
        if isinstance(getattr(self.model, self.hash_key), NumberAttribute):
            hash_key = int(hash_key)

        try:
            return self.model.get(hash_key)
        except self.model.DoesNotExist:
            return None


class OneToMany(Relationship):
    attr_type = STRING_SET

    def serialize(self, models):
        return [getattr(model, self.hash_key) for model in models]

    def deserialize(self, hash_keys):
        if isinstance(getattr(self.model, self.hash_key), NumberAttribute):
            hash_keys = map(int, hash_keys)

        try:
            return self.model.batch_get(hash_keys)
        except self.model.DoesNotExist:
            return None
