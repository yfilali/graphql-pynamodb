from graphene import Field, GlobalID, Int, Interface, ObjectType
from graphene.relay import Node, is_node
from mock import patch

from ..registry import Registry
from ..types import PynamoObjectType
from .models import Article, Reporter

registry = Registry()


class Character(PynamoObjectType):
    '''Character description'''

    class Meta:
        model = Reporter
        registry = registry


class Human(PynamoObjectType):
    '''Human description'''

    pub_date = Int()

    class Meta:
        model = Article
        exclude_fields = ('id',)
        registry = registry
        interfaces = (Node,)


def test_pynamo_interface():
    assert issubclass(Node, Interface)
    assert issubclass(Node, Node)


@patch('graphene_pynamodb.tests.models.Article.get', return_value=Article(id=1))
def test_pynamo_get_node(get):
    human = Human.get_node(1, None, None)
    get.assert_called_with(1)
    assert human.id == 1


def test_objecttype_registered():
    assert issubclass(Character, ObjectType)
    assert Character._meta.model == Reporter
    assert list(Character._meta.fields.keys()) == [
        'articles',
        'email',
        'favorite_article',
        'first_name',
        'id',
        'last_name',
        'pets']


def test_node_idfield():
    idfield = Human._meta.fields['id']
    assert isinstance(idfield, GlobalID)


def test_node_replacedfield():
    idfield = Human._meta.fields['pub_date']
    assert isinstance(idfield, Field)
    assert idfield.type == Int


def test_object_type():
    assert issubclass(Human, ObjectType)
    assert list(Human._meta.fields.keys()) == ['id', 'headline', 'reporter_id', 'pub_date']
    assert is_node(Human)
