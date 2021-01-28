import inspect
import json
from collections import OrderedDict

from pynamodb import attributes
from singledispatch import singledispatch

from graphene import ID, Boolean, Dynamic, Field, Float, Int, List, String
from graphene.types import ObjectType
from graphene.types.json import JSONString
from graphene.types.resolver import default_resolver
from graphene_pynamodb import relationships
from graphene_pynamodb.fields import PynamoConnectionField
from graphene_pynamodb.registry import Registry
from graphene_pynamodb.relationships import OneToMany, OneToOne


@singledispatch
def convert_pynamo_attribute(type, attribute, registry=None):
    raise Exception(
        "Don't know how to convert the PynamoDB attribute %s (%s)"
        % (attribute, attribute.__class__)
    )


@convert_pynamo_attribute.register(attributes.BinaryAttribute)
@convert_pynamo_attribute.register(attributes.UnicodeAttribute)
def convert_column_to_string(type, attribute, registry=None):
    if attribute.is_hash_key:
        return ID(description=attribute.attr_name, required=not attribute.null)

    return String(
        description=getattr(attribute, "attr_name"),
        required=not (getattr(attribute, "null", True)),
    )


@convert_pynamo_attribute.register(attributes.UTCDateTimeAttribute)
def convert_date_to_string(type, attribute, registry=None):
    return String(
        description=getattr(attribute, "attr_name"),
        required=not (getattr(attribute, "null", True)),
    )


@convert_pynamo_attribute.register(relationships.Relationship)
def convert_relationship_to_dynamic(type, attribute, registry=None):
    def dynamic_type():
        _type = registry.get_type_for_model(attribute.model)
        if not _type:
            return None

        if isinstance(attribute, OneToOne):
            return Field(_type)

        if isinstance(attribute, OneToMany):
            if _type._meta.connection:
                return PynamoConnectionField(_type)
            return Field(List(_type))

    return Dynamic(dynamic_type)


@convert_pynamo_attribute.register(attributes.NumberAttribute)
def convert_column_to_float_or_id(type, attribute, registry=None):
    if attribute.is_hash_key:
        return ID(description=attribute.attr_name, required=not attribute.null)

    return Float(description=attribute.attr_name, required=not attribute.null)


@convert_pynamo_attribute.register(attributes.BooleanAttribute)
def convert_column_to_boolean(type, attribute, registry=None):
    return Boolean(description=attribute.attr_name, required=not attribute.null)


@convert_pynamo_attribute.register(attributes.UnicodeSetAttribute)
@convert_pynamo_attribute.register(attributes.NumberSetAttribute)
@convert_pynamo_attribute.register(attributes.BinarySetAttribute)
def convert_scalar_list_to_list(type, attribute, registry=None):
    return List(String, description=attribute.attr_name)


@convert_pynamo_attribute.register(attributes.JSONAttribute)
def convert_json_to_string(type, attribute, registry=None):
    return JSONString(description=attribute.attr_name, required=not attribute.null)


class MapToJSONString(JSONString):
    """JSON String Converter for MapAttribute"""

    @staticmethod
    def serialize(dt):
        return json.dumps(dt.as_dict())


class ListOfMapToObject(JSONString):
    """JSON String Converter for List of MapAttribute"""

    @staticmethod
    def serialize(dt):
        if len(dt) == 0:
            return list()

        if issubclass(type(dt[0]), attributes.MapAttribute):
            return list(map(lambda x: x.as_dict(), dt))
        else:
            return dt


def map_attribute_to_object_type(attribute, registry: Registry):
    if not hasattr(registry, "map_attr_types"):
        registry.map_attr_types = {}
    if attribute in registry.map_attr_types:
        return registry.map_attr_types[attribute]

    fields = OrderedDict()
    for name, attr in attribute.get_attributes().items():
        fields[name] = convert_pynamo_attribute(attr, attr, registry)

    map_attribute_type = type(
        f"MapAttribute_{attribute.__name__}", (ObjectType,), fields,
    )

    registry.map_attr_types[attribute] = map_attribute_type
    return map_attribute_type


@convert_pynamo_attribute.register(attributes.MapAttribute)
def convert_map_to_object_type(attribute, _, registry=None):
    try:
        name = attribute.attr_name
    except (KeyError, AttributeError):
        name = "MapAttribute"
    required = not attribute.null if hasattr(attribute, "null") else False
    return map_attribute_to_object_type(attribute, registry)(
        description=name, required=required
    )


def list_resolver(
    parent,
    info,
    index: int = None,
    start_index: int = None,
    end_index: int = None,
    **kwargs,
):
    data = default_resolver(
        attname=info.field_name, default_value=None, root=parent, info=info, **kwargs
    )
    if index is not None:
        return [data[index]]
    if (start_index is not None) and (end_index is not None):
        return data[start_index:end_index]
    if start_index is not None:
        return data[start_index:]
    if end_index is not None:
        return data[:end_index]
    return data


@convert_pynamo_attribute.register(attributes.ListAttribute)
def convert_list_to_list(type, attribute, registry=None):
    kwargs = dict(
        resolver=list_resolver,
        index=Int(description="Return element at the position"),
        start_index=Int(description="Start of the slice of the list"),
        end_index=Int(
            description="End of the slice of the list. Negative numbers can be given to access from the end."
        ),
    )

    if attribute.element_type and inspect.isclass(attribute.element_type):
        try:
            name = attribute.attr_name
        except KeyError:
            name = attribute.element_type.__name__

        required = not attribute.null if hasattr(attribute, "null") else False

        if issubclass(attribute.element_type, attributes.MapAttribute):
            cls = map_attribute_to_object_type(attribute.element_type, registry)
        elif issubclass(attribute.element_type, attributes.NumberAttribute):
            cls = Int
        elif issubclass(attribute.element_type, attributes.BooleanAttribute):
            cls = Boolean
        else:
            cls = String

        return List(cls, description=name, required=required, **kwargs,)
    else:
        return List(String, description=attribute.attr_name, **kwargs)
