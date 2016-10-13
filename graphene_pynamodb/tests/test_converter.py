import graphene
from graphene import Dynamic
from graphene import Node
from graphene.types.json import JSONString
from py.test import raises
from pynamodb.attributes import (BinaryAttribute, BinarySetAttribute,
                                 BooleanAttribute, JSONAttribute,
                                 NumberAttribute, NumberSetAttribute,
                                 UnicodeAttribute, UnicodeSetAttribute,
                                 UTCDateTimeAttribute)

from graphene_pynamodb import PynamoObjectType
from graphene_pynamodb.tests.models import Article, Reporter
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


def test_should_number_convert_int():
    assert_attribute_conversion(NumberAttribute(), graphene.Int)


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


# TODO keeping turned off until I implement some sort of relationships on top of PynamoDB
# PS: (DynamoDB is not relational)
# def test_should_manytomany_convert_connectionorlist():
#     registry = Registry()
#     dynamic_field = convert_relationship(Reporter.pets.property, registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     assert not dynamic_field.get_type()

#
# def test_should_manytomany_convert_connectionorlist_list():
#     class A(PynamoObjectType):
#         class Meta:
#             model = Pet
#
#     dynamic_field = convert_relationship(Reporter.pets.property, A._meta.registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     graphene_type = dynamic_field.get_type()
#     assert isinstance(graphene_type, graphene.Field)
#     assert isinstance(graphene_type.type, graphene.List)
#     assert graphene_type.type.of_type == A


# def test_should_manytomany_convert_connectionorlist_connection():
#     class A(PynamoObjectType):
#         class Meta:
#             model = Pet
#             interfaces = (Node,)
#
#     dynamic_field = convert_relationship(Reporter.pets.property, A._meta.registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     assert isinstance(dynamic_field.get_type(), PynamoConnectionField)
#
#
# def test_should_manytoone_convert_connectionorlist():
#     registry = Registry()
#     dynamic_field = convert_relationship(Article.reporter.property, registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     assert not dynamic_field.get_type()
#
#
# def test_should_manytoone_convert_connectionorlist_list():
#     class A(PynamoObjectType):
#         class Meta:
#             model = Reporter
#
#     dynamic_field = convert_relationship(Article.reporter.property, A._meta.registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     graphene_type = dynamic_field.get_type()
#     assert isinstance(graphene_type, graphene.Field)
#     assert graphene_type.type == A
#
#
# def test_should_manytoone_convert_connectionorlist_connection():
#     class A(PynamoObjectType):
#         class Meta:
#             model = Reporter
#             interfaces = (Node,)
#
#     dynamic_field = convert_relationship(Article.reporter.property, A._meta.registry)
#     assert isinstance(dynamic_field, graphene.Dynamic)
#     graphene_type = dynamic_field.get_type()
#     assert isinstance(graphene_type, graphene.Field)
#     assert graphene_type.type == A
#
#
def test_should_onetoone_convert_field():
    class A(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    dynamic_field = convert_pynamo_attribute(Reporter.favorite_article, Reporter.favorite_article, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == A


def test_should_onetomany_convert_field():
    class A(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    dynamic_field = convert_pynamo_attribute(Reporter.articles, Reporter.favorite_article, A._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == A
