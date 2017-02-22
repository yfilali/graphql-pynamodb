import graphene
import pytest
from graphene import Node
from mock import MagicMock
from wrapt import ObjectProxy

from .models import Reporter, Article
from ..relationships import OneToOne, OneToMany, RelationshipResult
from ..types import PynamoObjectType


def setup_fixtures():
    class ReporterType(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class ArticleType(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    reporter1 = Reporter(1, first_name="John", last_name="Snow")
    article1 = Article(1, headline="Hi!", reporter=reporter1)
    article2 = Article(2, headline="Lame Article", reporter=reporter1)
    reporter1.articles = [article1, article2]

    return {
        'ReporterType': ReporterType,
        'ArticleType': ArticleType,
        'reporter1': reporter1,
        'article1': article1,
        'article2': article2
    }


def test_relationships_should_resolve_well():
    fixtures = setup_fixtures()

    class Query(graphene.ObjectType):
        reporter = graphene.Field(fixtures["ReporterType"])
        articles = graphene.List(fixtures["ArticleType"])

        def resolve_reporter(self, *args, **kwargs):
            return fixtures["reporter1"]

        def resolve_articles(self, *args, **kwargs):
            return fixtures["reporter1"].articles

    query = '''
      query AuthorQuery {
        reporter {
          firstName,
          lastName,
          articles {
            edges {
              node {
                id
              }
            }
          }
        }
        articles {
          headline
          reporter {
            id
          }
        }
      }
    '''
    expected = {
        'reporter': {
            'firstName': 'John',
            'lastName': 'Snow',
            'articles': {
                'edges': [{
                    'node': {
                        'id': 'QXJ0aWNsZVR5cGU6MQ==',
                    }
                }, {
                    'node': {
                        'id': 'QXJ0aWNsZVR5cGU6Mg=='
                    }
                }]
            }
        },
        'articles': [{
            'headline': 'Hi!',
            'reporter': {
                'id': 'UmVwb3J0ZXJUeXBlOjE='
            }
        }, {
            'headline': 'Lame Article',
            'reporter': {
                'id': 'UmVwb3J0ZXJUeXBlOjE='
            }
        }]
    }

    schema = graphene.Schema(query=Query)

    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter'] == expected['reporter']
    assert all(item in result.data['articles'] for item in expected['articles'])


def test_relationships_should_raiseerror():
    with pytest.raises(TypeError):
        OneToOne(object)
    with pytest.raises(TypeError):
        OneToMany(object)


def test_onetoone_should_serialize_well():
    fixtures = setup_fixtures()
    relationship = OneToOne(Article)
    assert relationship.serialize(fixtures["article1"]) == "1"


def test_onetoone_should_deserialize_well():
    fixtures = setup_fixtures()
    relationship = OneToOne(Article)
    article = relationship.deserialize(1)
    assert isinstance(article, Article.__class__)
    assert article.id == fixtures["article1"].id
    assert article.headline == fixtures["article1"].headline


def test_onetomany_should_serialize_well():
    fixtures = setup_fixtures()
    relationship = OneToMany(Article)
    assert relationship.serialize([fixtures["article1"], fixtures["article2"]]) == [{'N': '1'}, {'N': '2'}]


def test_onetomany_should_deserialize_well():
    relationship = OneToMany(Article)

    articles = relationship.deserialize([1, 3])
    assert len(articles) == 2
    # test before db call (lazy)
    assert articles[0] == Article(1)
    assert articles[1] == Article(3)
    # test db call
    assert articles[0].headline == "Hi!"
    assert articles[1].headline == "My Article"


def test_result_should_be_lazy():
    MockArticle = ObjectProxy(Article)
    MockArticle.get = MagicMock(return_value=Article.get(1))
    relationship = RelationshipResult('id', 1, MockArticle)

    # test before db call (lazy)
    assert relationship.id == 1
    MockArticle.get.assert_not_called()
    # test db call only once
    assert relationship.headline == "Hi!"
    assert relationship.reporter.id == 1
    assert relationship.headline == "Hi!"
    MockArticle.get.assert_called_once_with(1)


def test_relationships_should_compare_well():
    article1 = Article(1, headline="test")
    article2 = Article(2, headline="test")
    rel1 = RelationshipResult('id', 1, Article)
    assert rel1 == article1
    assert rel1 != article2


def test_result_should_check_type():
    with pytest.raises(TypeError):
        RelationshipResult('id', 1, PynamoObjectType)


def test_onetoone_should_handle_not_being_lazy():
    MockArticle = ObjectProxy(Article)
    MockArticle.get = MagicMock(return_value=Article.get(1))
    relationship = OneToOne(MockArticle, lazy=False)
    article = relationship.deserialize(1)
    MockArticle.get.assert_called_once_with(1)

    # Access fields that would normally trigger laxy loading
    assert article.id == 1
    assert article.headline == "Hi!"
    assert article.reporter.id == 1
    assert article.headline == "Hi!"
    # make sure our call count is still 1
    MockArticle.get.assert_called_once_with(1)


def test_onetomany_should_handle_not_being_lazy():
    MockArticle = ObjectProxy(Article)
    MockArticle.get = MagicMock()
    MockArticle.batch_get = MagicMock(return_value=Article.batch_get([1, 3]))
    relationship = OneToMany(MockArticle, lazy=False)
    articles = list(relationship.deserialize([1, 3]))
    MockArticle.batch_get.assert_called_once()
    MockArticle.get.assert_not_called()
    # Access fields that would normally trigger laxy loading
    # order is not guaranteed in batch_get
    if articles[0].id == 1:
        assert articles[0].headline == "Hi!"
        assert articles[1].id == 3
        assert articles[1].headline == "My Article"
    else:
        assert articles[0].id == 3
        assert articles[0].headline == "My Article"
        assert articles[1].id == 1
        assert articles[1].headline == "Hi!"
    # make sure our call count is still 1
    MockArticle.batch_get.assert_called_once()
    MockArticle.get.assert_not_called()
