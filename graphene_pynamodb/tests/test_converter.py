import graphene
from graphene import Dynamic, relay
from graphene import Node
from graphene.types.json import JSONString
from pynamodb.attributes import (BinaryAttribute, BinarySetAttribute,
                                 BooleanAttribute, JSONAttribute,
                                 NumberAttribute, NumberSetAttribute,
                                 UnicodeAttribute, UnicodeSetAttribute,
                                 UTCDateTimeAttribute, MapAttribute, ListAttribute)
from pynamodb.models import Model
from pytest import raises

from graphene_pynamodb.relationships import OneToMany
from .models import Article, Reporter
from .. import PynamoConnectionField
from .. import PynamoObjectType
from ..converter import convert_pynamo_attribute


def assert_attribute_conversion(attribute, graphene_field, **kwargs):
    graphene_type = convert_pynamo_attribute(attribute, attribute)
    assert isinstance(graphene_type, graphene_field)
    field = graphene_type.Field()
    return field


def test_should_unknown_pynamo_field_raise_exception():
    with raises(Exception) as excinfo:
        convert_pynamo_attribute(None, None, None)
    assert 'Don\'t know how to convert the PynamoDB attribute' in str(excinfo.value)


def test_should_datetime_convert_string():
    assert_attribute_conversion(UTCDateTimeAttribute(), graphene.String)


def test_should_string_convert_string():
    assert_attribute_conversion(UnicodeAttribute(), graphene.String)


def test_should_binary_convert_string():
    assert_attribute_conversion(BinaryAttribute(), graphene.String)


def test_should_number_convert_float():
    assert_attribute_conversion(NumberAttribute(), graphene.Float)


def test_should_boolean_convert_boolean():
    assert_attribute_conversion(BooleanAttribute(), graphene.Boolean)


def test_should_string_set_convert_list():
    assert_attribute_conversion(UnicodeSetAttribute(), graphene.List)


def test_should_number_set_convert_list():
    assert_attribute_conversion(NumberSetAttribute(), graphene.List)


def test_should_binary_set_convert_list():
    assert_attribute_conversion(BinarySetAttribute(), graphene.List)


def test_should_jsontype_convert_jsonstring():
    assert_attribute_conversion(JSONAttribute(), JSONString)


def test_should_onetoone_convert_field():
    class A(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = [relay.Node]

    dynamic_field = convert_pynamo_attribute(Reporter.favorite_article, Reporter.favorite_article, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == A


def test_should_onetomany_convert_nonnode_field():
    class A(PynamoObjectType):
        class Meta:
            model = Article

    dynamic_field = convert_pynamo_attribute(Reporter.articles, Reporter.articles, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == graphene.List(A)


def test_should_onetomany_none_for_unknown_type():
    class ModelA(Model):
        pass

    class ModelB(Model):
        a = OneToMany(ModelA)

    class A(PynamoObjectType):
        class Meta:
            model = ModelB

    dynamic_field = convert_pynamo_attribute(ModelB.a, ModelB.a, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    assert dynamic_field.get_type() is None


def test_should_onetomany_convert_field():
    class A(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    dynamic_field = convert_pynamo_attribute(Reporter.articles, Reporter.articles, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, PynamoConnectionField)


def test_should_map_converts_to_json():
    assert_attribute_conversion(MapAttribute(), JSONString)


def test_should_list_convert_list():
    assert_attribute_conversion(ListAttribute(), graphene.List)
