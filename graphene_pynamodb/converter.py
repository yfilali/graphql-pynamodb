from graphene import Dynamic
from graphene import Field
from graphene import ID, Boolean, Int, List, String
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
@convert_pynamo_attribute.register(attributes.UTCDateTimeAttribute)
def convert_column_to_string(type, attribute, registry=None):
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

        return None

    return Dynamic(dynamic_type)


@convert_pynamo_attribute.register(attributes.NumberAttribute)
def convert_column_to_int_or_id(type, attribute, registry=None):
    if attribute.is_hash_key:
        return ID(description=attribute.attr_name, required=not attribute.null)
    else:
        return Int(description=attribute.attr_name, required=not attribute.null)


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
