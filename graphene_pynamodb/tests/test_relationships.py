import logging

import graphene
from graphene import Node

from graphene_pynamodb.relationships import OneToOne, OneToMany
from .models import Reporter, Article
from ..types import PynamoObjectType

logging.basicConfig()


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
    article1 = Article(1, headline="Awesome Article", reporter=reporter1)
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
            'headline': 'Awesome Article',
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


def test_onetoone_should_serialize_well():
    fixtures = setup_fixtures()
    relationship = OneToOne(Article)
    assert relationship.serialize(fixtures["article1"]) == "1"


def test_onetoone_should_deserialize_well():
    fixtures = setup_fixtures()
    relationship = OneToOne(Article)
    article = relationship.deserialize(2)
    assert isinstance(article, Article.__class__)
    assert article.id == fixtures["article2"].id


def test_onetomany_should_serialize_well():
    fixtures = setup_fixtures()
    relationship = OneToMany(Article)
    assert relationship.serialize([fixtures["article1"], fixtures["article2"]]) == ['1', '2']


def test_onetomany_should_deserialize_well():
    relationship = OneToMany(Article)

    articles = relationship.deserialize([1, 3])
    print(articles)

    assert len(articles) == 2
    assert isinstance(articles[0], Article.__class__)
    assert isinstance(articles[1], Article.__class__)
    assert articles[0].id == 1
    assert articles[1].id == 3
    assert articles[0].headline == "Hi!"
    assert articles[1].headline == "My Article"
