import json
from typing import Tuple

from graphql_relay import from_global_id, to_global_id
from pynamodb.attributes import Attribute
from pynamodb.models import Model

import graphene

MODEL_KEY_REGISTRY = {}


def get_key_name(model):
    if not issubclass(model, Model):
        raise TypeError("Invalid type passed to get_key_name: %s" % model.__class__)

    if model in MODEL_KEY_REGISTRY:
        return MODEL_KEY_REGISTRY[model]

    for attr in model.get_attributes().values():
        if isinstance(attr, Attribute) and attr.is_hash_key:
            MODEL_KEY_REGISTRY[model] = attr.attr_name
            return attr.attr_name


def connection_for_type(_type):
    class Connection(graphene.relay.Connection):
        total_count = graphene.Int()

        class Meta:
            name = _type._meta.name + "Connection"
            node = _type

        def resolve_total_count(self, args, context, info):
            return self.total_count if hasattr(self, "total_count") else len(self.edges)

    return Connection


def to_cursor(item: Model) -> str:
    data = {}  # this will be same as last_evaluated_key returned by PageIterator
    for name, attr in item.get_attributes().items():
        if attr.is_hash_key or attr.is_range_key:
            data[name] = item._serialize_value(attr, getattr(item, name))
    return to_global_id(type(item).__name__, json.dumps(data))


def from_cursor(cursor: str) -> Tuple[str, dict]:
    model, data = from_global_id(cursor)
    return model, json.loads(data)
