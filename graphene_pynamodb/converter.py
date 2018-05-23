import json

from graphene import Dynamic, Float
from graphene import Field
from graphene import ID, Boolean, List, String
from graphene import is_node
from graphene.types.json import JSONString
from pynamodb import attributes
from singledispatch import singledispatch

from graphene_pynamodb import relationships
from graphene_pynamodb.fields import PynamoConnectionField
from graphene_pynamodb.relationships import OneToOne, OneToMany


@singledispatch
def convert_pynamo_attribute(type, attribute, registry=None):
    raise Exception(
        "Don't know how to convert the PynamoDB attribute %s (%s)" % (attribute, attribute.__class__))


@convert_pynamo_attribute.register(attributes.BinaryAttribute)
@convert_pynamo_attribute.register(attributes.UnicodeAttribute)
def convert_column_to_string(type, attribute, registry=None):
    if attribute.is_hash_key:
        return ID(description=attribute.attr_name, required=not attribute.null)

    return String(description=getattr(attribute, 'attr_name'),
                  required=not (getattr(attribute, 'null', True)))


@convert_pynamo_attribute.register(attributes.UTCDateTimeAttribute)
def convert_date_to_string(type, attribute, registry=None):
    return String(description=getattr(attribute, 'attr_name'),
                  required=not (getattr(attribute, 'null', True)))


@convert_pynamo_attribute.register(relationships.Relationship)
def convert_relationship_to_dynamic(type, attribute, registry=None):
    def dynamic_type():
        _type = registry.get_type_for_model(attribute.model)
        if not _type:
            return None

        if isinstance(attribute, OneToOne):
            return Field(_type)

        if isinstance(attribute, OneToMany):
            if is_node(_type):
                return PynamoConnectionField(_type)
            return Field(List(_type))

    return Dynamic(dynamic_type)


@convert_pynamo_attribute.register(attributes.NumberAttribute)
def convert_column_to_float_or_id(type, attribute, registry=None):
    if attribute.is_hash_key:
        return ID(description=attribute.attr_name, required=not attribute.null)

    return Float(description=attribute.attr_name, required=not attribute.null)


@convert_pynamo_attribute.register(attributes.LegacyBooleanAttribute)
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
    '''JSON String Converter for MapAttribute'''

    @staticmethod
    def serialize(dt):
        return json.dumps(dt.as_dict())


@convert_pynamo_attribute.register(attributes.MapAttribute)
def convert_map_to_json(type, attribute, registry=None):
    try:
        name = attribute.attr_name
    except KeyError:
        name = "MapAttribute"
    required = not attribute.null if hasattr(attribute, 'null') else False
    return MapToJSONString(description=name, required=required)


@convert_pynamo_attribute.register(attributes.ListAttribute)
def convert_list_to_list(type, attribute, registry=None):
    return List(String, description=attribute.attr_name)
