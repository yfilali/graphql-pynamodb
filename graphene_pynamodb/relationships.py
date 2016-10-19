from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.constants import STRING, STRING_SET
from pynamodb.models import Model
from six import string_types
from wrapt import ObjectProxy


class RelationshipResult(ObjectProxy):
    def __init__(self, key_name, key, obj):
        if isinstance(obj, type) and not issubclass(obj, Model):
            raise TypeError("Invalid class passed to RelationshipResult, expected a Model class, got %s" % type(obj))
        super(RelationshipResult, self).__init__(obj)
        self._self_key = key
        self._self_key_name = key_name
        self._self_model = obj

    def __getattr__(self, name):
        if name == self._self_key_name:
            return self._self_key
        if not name.startswith('_') and isinstance(self.__wrapped__, type):
            self.__wrapped__ = self._self_model.get(self._self_key)
        return super(RelationshipResult, self).__getattr__(name)

    def __eq__(self, other):
        return isinstance(other, self._self_model) and self._self_key == getattr(other, self._self_key_name)

    def __ne__(self, other):
        return not self.__eq__(other)


class Relationship(Attribute):
    _models = None

    @classmethod
    def sub_classes(cls, klass):
        return klass.__subclasses__() + [g for s in klass.__subclasses__() for g in Relationship.sub_classes(s)]

    @classmethod
    def get_model(cls, model_name):
        # Resolve a model name into a model class by looking in all Model subclasses
        if not Relationship._models:
            Relationship._models = Relationship.sub_classes(Model)
        return next((model for model in Relationship._models if model.__name__ == model_name), None)

    def __init__(self, model, hash_key="id", lazy=True, **args):
        if not isinstance(model, string_types) and not issubclass(model, Model):
            raise TypeError("Expected PynamoDB Model argument, got: %s " % model.__class__.__name__)

        Attribute.__init__(self, **args)
        self._model = model
        self.hash_key_name = hash_key
        self._lazy = lazy

    @property
    def model(self):
        if isinstance(self._model, string_types):
            self._model = Relationship.get_model(self._model)

        return self._model


class OneToOne(Relationship):
    attr_type = STRING

    def serialize(self, model):
        return str(getattr(model, self.hash_key_name))

    def deserialize(self, hash_key):
        if isinstance(getattr(self.model, self.hash_key_name), NumberAttribute):
            hash_key = int(hash_key)

        if self._lazy:
            return RelationshipResult(self.hash_key_name, hash_key, self.model)
        else:
            return self.model.get(hash_key)


class OneToMany(Relationship):
    attr_type = STRING_SET

    def serialize(self, models):
        return [str(getattr(model, self.hash_key_name)) for model in models]

    def deserialize(self, hash_keys):
        if isinstance(getattr(self.model, self.hash_key_name), NumberAttribute):
            hash_keys = map(int, hash_keys)

        if self._lazy:
            return [RelationshipResult(self.hash_key_name, hash_key, self.model) for hash_key in hash_keys]
        else:
            return self.model.batch_get(hash_keys)
