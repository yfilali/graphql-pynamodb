import graphene
from pynamodb.attributes import Attribute
from pynamodb.models import Model

MODEL_KEY_REGISTRY = {}


def get_key_name(model):
    if not issubclass(model, Model):
        raise TypeError("Invalid type passed to get_key_name: %s" % model.__class__)

    if model in MODEL_KEY_REGISTRY:
        return MODEL_KEY_REGISTRY[model]

    for attr in vars(model):
        attr = getattr(model, attr)
        if isinstance(attr, Attribute) and attr.is_hash_key:
            MODEL_KEY_REGISTRY[model] = attr.attr_name
            return attr.attr_name


def connection_for_type(_type):
    class Connection(graphene.relay.Connection):
        total_count = graphene.Int()

        class Meta:
            name = _type._meta.name + 'Connection'
            node = _type

        def resolve_total_count(self, args, context, info):
            return self.total_count if hasattr(self, "total_count") else len(self.edges)

    return Connection
