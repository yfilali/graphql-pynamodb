from collections import OrderedDict
from inspect import isclass

from graphene import Field, Connection, Node
from graphene.relay import is_node
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs
from pynamodb.attributes import Attribute, NumberAttribute
from pynamodb.models import Model

from .converter import convert_pynamo_attribute
from .registry import Registry, get_global_registry
from .relationships import RelationshipResult
from .utils import get_key_name, connection_for_type


def get_model_fields(model, excluding=None):
    if excluding is None:
        excluding = []
    attributes = dict()
    for attr_name in vars(model):
        if attr_name in excluding:
            continue
        attr = getattr(model, attr_name)
        if isinstance(attr, Attribute):
            attributes[attr_name] = attr

    return OrderedDict(sorted(attributes.items(), key=lambda t: t[0]))


def construct_fields(model, registry, only_fields, exclude_fields):
    inspected_model = get_model_fields(model)

    fields = OrderedDict()

    for name, attribute in inspected_model.items():
        is_not_in_only = only_fields and name not in only_fields
        is_already_created = name in fields
        is_excluded = name in exclude_fields or is_already_created
        if is_not_in_only or is_excluded:
            # We skip this field if we specify only_fields and is not
            # in there. Or when we excldue this field in exclude_fields
            continue
        converted_column = convert_pynamo_attribute(attribute, attribute, registry)
        fields[name] = converted_column

    return fields


class PynamoObjectTypeOptions(ObjectTypeOptions):
    model = None  # type: Model
    registry = None  # type: Registry
    connection = None  # type: Type[Connection]
    id = None  # type: str


class PynamoObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, model=None, registry=None, skip_registry=False,
                                    only_fields=(), exclude_fields=(), connection=None,
                                    use_connection=None, interfaces=(), id=None, **options):
        assert model and isclass(model) and issubclass(model, Model), (
            'You need to pass a valid PynamoDB Model in '
            '{}.Meta, received "{}".'
        ).format(cls.__name__, model)

        if not registry:
            registry = get_global_registry()

        assert isinstance(registry, Registry), (
            'The attribute registry in {} needs to be an instance of '
            'Registry, received "{}".'
        ).format(cls.__name__, registry)

        pynamo_fields = yank_fields_from_attrs(
            construct_fields(model, registry, only_fields, exclude_fields),
            _as=Field,
        )

        if use_connection is None and interfaces:
            use_connection = any((issubclass(interface, Node) for interface in interfaces))

        if use_connection and not connection:
            # We create the connection automatically
            connection = Connection.create_type('{}Connection'.format(cls.__name__), node=cls)

        if connection is not None:
            assert issubclass(connection, Connection), (
                "The connection must be a Connection. Received {}"
            ).format(connection.__name__)

        _meta = PynamoObjectTypeOptions(cls)
        _meta.model = model
        _meta.registry = registry
        _meta.fields = pynamo_fields
        _meta.connection = connection
        _meta.id = id or 'id'

        super(PynamoObjectType, cls).__init_subclass_with_meta__(_meta=_meta, interfaces=interfaces, **options)

        if not skip_registry:
            registry.register(cls)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, RelationshipResult) and root.__wrapped__ == cls._meta.model:
            return True
        return isinstance(root, cls._meta.model)

    @classmethod
    def get_node(cls, info, id):
        if isinstance(getattr(cls._meta.model, get_key_name(cls._meta.model)), NumberAttribute):
            return cls._meta.model.get(int(id))
        else:
            return cls._meta.model.get(id)

    def resolve_id(self, info):
        graphene_type = info.parent_type.graphene_type
        if is_node(graphene_type):
            return getattr(self, get_key_name(graphene_type._meta.model))

    @classmethod
    def get_connection(cls):
        return connection_for_type(cls)
