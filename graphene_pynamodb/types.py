import inspect
from collections import OrderedDict

import six
from graphene import Field
from graphene.relay import is_node
from graphene.types.objecttype import ObjectType, ObjectTypeMeta
from graphene.types.options import Options
from graphene.types.utils import merge, yank_fields_from_attrs
from graphene.utils.is_base_type import is_base_type
from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.connection.base import MetaTable
from pynamodb.exceptions import DoesNotExist
from pynamodb.models import Model

from .converter import convert_pynamo_attribute
from .registry import Registry, get_global_registry
from .relationships import RelationshipResult


def get_model_fields(model):
    attributes = dict()
    for item in dir(model):
        try:
            item_cls = getattr(getattr(model, item), "__class__", None)
        except AttributeError:
            continue
        if item_cls is None:
            continue
        if issubclass(item_cls, (Attribute,)):
            attributes[item] = getattr(model, item)

    return OrderedDict(sorted(attributes.items(), key=lambda t: t[0]))


def construct_fields(options):
    only_fields = options.only_fields
    exclude_fields = options.exclude_fields
    inspected_model = get_model_fields(options.model)

    fields = OrderedDict()

    for name, attribute in inspected_model.items():
        is_not_in_only = only_fields and name not in only_fields
        is_already_created = name in options.fields
        is_excluded = name in exclude_fields or is_already_created
        if is_not_in_only or is_excluded:
            # We skip this field if we specify only_fields and is not
            # in there. Or when we excldue this field in exclude_fields
            continue
        converted_column = convert_pynamo_attribute(attribute, attribute, options.registry)
        fields[name] = converted_column

    return fields


class PynamoObjectTypeMeta(ObjectTypeMeta):
    @staticmethod
    def __new__(cls, name, bases, attrs):
        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        if not is_base_type(bases, PynamoObjectTypeMeta):
            return type.__new__(cls, name, bases, attrs)

        options = Options(
            attrs.pop('Meta', None),
            name=name,
            description=attrs.pop('__doc__', None),
            model=None,
            local_fields=None,
            only_fields=(),
            exclude_fields=(),
            id='id',
            interfaces=(),
            registry=None
        )

        if not options.registry:
            options.registry = get_global_registry()
        assert isinstance(options.registry, Registry), (
            'The attribute registry in {}.Meta needs to be an'
            ' instance of Registry, received "{}".'
        ).format(name, options.registry)

        assert (inspect.isclass(options.model) and issubclass(options.model, Model)), (
            'You need to pass a valid PynamoDB Model in '
            '{}.Meta, received "{}".'
        ).format(name, options.model)

        cls = ObjectTypeMeta.__new__(cls, name, bases, dict(attrs, _meta=options))

        options.registry.register(cls)

        options.pynamo_fields = yank_fields_from_attrs(
            construct_fields(options),
            _as=Field,
        )
        options.fields = merge(
            options.interface_fields,
            options.pynamo_fields,
            options.base_fields,
            options.local_fields
        )

        return cls


class PynamoObjectType(six.with_metaclass(PynamoObjectTypeMeta, ObjectType)):
    @classmethod
    def inspect_model(cls, model):
        if model._meta_table is None:
            model._meta_table = MetaTable(model._get_connection().describe_table())

    @classmethod
    def is_type_of(cls, root, context, info):
        if isinstance(root, cls):
            return True
        if isinstance(root, RelationshipResult) and root.__wrapped__ == cls._meta.model:
            return True
        return isinstance(root, cls._meta.model)

    @classmethod
    def get_query(cls, context):
        query = getattr(cls._meta.model, 'scan', None)
        if not query:
            raise Exception('A query in the model Base is required for querying.\n Read more '
                            'http://pynamodb.readthedocs.io/en/latest/quickstart.html?highlight=query#querying')
        return query

    @classmethod
    def get_node(cls, id, context, info):
        try:
            PynamoObjectType.inspect_model(cls._meta.model)
            if isinstance(getattr(cls._meta.model, cls._meta.model._meta_table.hash_keyname), NumberAttribute):
                return cls._meta.model.get(int(id))
            else:
                return cls._meta.model.get(id)
        except AttributeError:
            return cls._meta.model.get(id)
        except DoesNotExist:
            return None

    def resolve_id(self, args, context, info):
        graphene_type = info.parent_type.graphene_type
        if is_node(graphene_type):
            PynamoObjectType.inspect_model(graphene_type._meta.model)
            return getattr(self, graphene_type._meta.model._meta_table.hash_keyname)

        return getattr(args, graphene_type._meta.id)
