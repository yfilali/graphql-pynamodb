from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.constants import STRING, STRING_SET
from pynamodb.models import Model
from six import string_types
from wrapt import ObjectProxy


class RelationshipResult(ObjectProxy):
    _key = None
    _key_name = ''
    _model = None

    def __init__(self, key_name, key, obj):
        super(RelationshipResult, self).__init__(obj)
        self._key = key
        self._key_name = key_name
        self._model = obj

    def __getattr__(self, name):
        # If we are being to lookup '__wrapped__' then the
        # '__init__()' method cannot have been called.
        if name == '__wrapped__':
            raise ValueError('wrapper has not been initialised')
        if name.startswith('_'):
            return getattr(self.__wrapped__, name)
        if name == self._key_name:
            return self._key
        if isinstance(self.__wrapped__, type) and issubclass(self.__wrapped__, Model):
            self.__wrapped__ = self.__wrapped__.get(self._key)
        return getattr(self.__wrapped__, name)

    def __eq__(self, other):
        # Shallow compare by id for relationship purposes
        if isinstance(self.__model__, type) and issubclass(self.__model__, Model):
            return isinstance(other, self.__model__) and self.__key__ == getattr(other, self.__key_name__)
        else:
            return (self.__model__.__class__ == other.__class__) and self.__key__ == getattr(other, self.__key_name__)

    def __ne__(self, other):
        return self.__model__ != other


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

        try:
            if self._lazy:
                return RelationshipResult(self.hash_key_name, hash_key, self.model)
            else:
                return self.model.get(hash_key)
        except self.model.DoesNotExist:
            return None


class OneToMany(Relationship):
    attr_type = STRING_SET

    def serialize(self, models):
        return [str(getattr(model, self.hash_key_name)) for model in models]

    def deserialize(self, hash_keys):
        if isinstance(getattr(self.model, self.hash_key_name), NumberAttribute):
            hash_keys = map(int, hash_keys)

        try:
            if self._lazy:
                return [RelationshipResult(self.hash_key_name, hash_key, self.model) for hash_key in hash_keys]
            else:
                return self.model.get_batch(hash_keys)
        except self.model.DoesNotExist:
            return None
