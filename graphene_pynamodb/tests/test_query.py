import logging

import graphene
from graphene.relay import Node

from .models import Article, Editor, Reporter
from ..fields import PynamoConnectionField
from ..types import PynamoObjectType

logging.basicConfig()


def setup_fixtures():
    for model in [Reporter, Article, Editor]:
        if not model.exists():
            model.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

        reporter = Reporter(id=1, first_name='ABA', last_name='X')
        reporter.save()
        reporter2 = Reporter(id=2, first_name='ABO', last_name='Y')
        reporter2.save()
        article = Article(id=1, headline='Hi!')
        article.reporter = reporter
        article.save()
        article2 = Article(id=3, headline='My Article')
        article2.reporter = reporter
        article2.save()
        editor = Editor(id=1, name="John")
        editor.save()


def test_should_query_well():
    setup_fixtures()

    class ReporterType(PynamoObjectType):
        class Meta:
            model = Reporter

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        reporters = graphene.List(ReporterType)

        def resolve_reporter(self, *args, **kwargs):
            return next(Reporter.query(1))

        def resolve_reporters(self, *args, **kwargs):
            return Reporter.scan()

    query = '''
        query ReporterQuery {
          reporter {
            firstName,
            lastName,
            email
          }
          reporters {
            firstName
          }
        }
    '''
    expected = {
        'reporter': {
            'email': None,
            'firstName': 'ABA',
            'lastName': 'X'
        },
        'reporters': [{
            'firstName': 'ABO',
        }, {
            'firstName': 'ABA',
        }]
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter'] == expected['reporter']
    assert all(item in result.data['reporters'] for item in expected['reporters'])


def test_should_node():
    setup_fixtures()

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, id, context, info):
            return Reporter(id=2, first_name='Cookie Monster')

    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

        @classmethod
        def get_node(cls, id, context, info):
            return Article(id=1, headline='Article node')

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)
        article = graphene.Field(ArticleNode)
        all_articles = PynamoConnectionField(ArticleNode)

        def resolve_reporter(self, *args, **kwargs):
            return next(Reporter.query(1))

        def resolve_article(self, *args, **kwargs):
            return next(Article.query(1))

    query = '''
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles {
              edges {
                node {
                  headline
                }
              }
            }
            lastName,
            email
          }
          allArticles {
            edges {
              node {
                headline
              }
            }
          }
          myArticle: node(id:"QXJ0aWNsZU5vZGU6MQ==") {
            id
            ... on ReporterNode {
                firstName
            }
            ... on ArticleNode {
                headline
            }
          }
        }
    '''
    expected = {
        'reporter': {
            'id': 'UmVwb3J0ZXJOb2RlOjE=',
            'firstName': 'ABA',
            'lastName': 'X',
            'email': None,
            'articles': {
                'edges': [
                    {
                        'node': {
                            'headline': 'Hi!'
                        }
                    },
                    {
                        'node': {
                            'headline': 'My Article'
                        }
                    }
                ]
            }
        },
        'allArticles': {
            'edges': [{
                'node': {
                    'headline': 'Hi!'
                }
            }]
        },
        'myArticle': {
            'id': 'QXJ0aWNsZU5vZGU6MQ==',
            'headline': 'Article node'
        }
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert all(item in expected["reporter"] for item in result.data["reporter"])
    assert all(item in expected["reporter"]["articles"] for item in result.data["reporter"]["articles"])
    assert result.data["myArticle"] == expected["myArticle"]
    assert all(item in result.data["allArticles"] for item in expected['allArticles'])


def test_should_custom_identifier():
    setup_fixtures()

    class EditorNode(PynamoObjectType):
        class Meta:
            model = Editor
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        all_editors = PynamoConnectionField(EditorNode)

    query = '''
        query EditorQuery {
          allEditors {
            edges {
                node {
                    id,
                    name
                }
            }
          },
          node(id: "RWRpdG9yTm9kZTox") {
            ...on EditorNode {
              name
            }
          }
        }
    '''
    expected = {
        'allEditors': {
            'edges': [{
                'node': {
                    'id': 'RWRpdG9yTm9kZTox',
                    'name': 'John'
                }
            }]
        },
        'node': {
            'name': 'John'
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data["allEditors"] == expected["allEditors"]


def test_should_mutate_well():
    setup_fixtures()

    class EditorNode(PynamoObjectType):
        class Meta:
            model = Editor
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, id, info):
            return Reporter(id=2, first_name='Cookie Monster')

    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class CreateArticle(graphene.Mutation):
        class Input:
            headline = graphene.String()
            reporter_id = graphene.ID()

        ok = graphene.Boolean()
        article = graphene.Field(ArticleNode)

        @classmethod
        def mutate(cls, instance, args, context, info):
            new_article = Article(
                id=3,
                headline=args.get('headline'),
                reporter=Reporter.get(int(args.get('reporter_id'))),
            )
            new_article.save()
            ok = True

            return CreateArticle(article=new_article, ok=ok)

    class Query(graphene.ObjectType):
        node = Node.Field()

    class Mutation(graphene.ObjectType):
        create_article = CreateArticle.Field()

    query = '''
        mutation ArticleCreator {
          createArticle(
            headline: "My Article"
            reporterId: "1"
          ) {
            ok
            article {
              headline
              reporter {
                id
              }
            }
          }
        }
    '''
    expected = {
        'createArticle': {
            'ok': True,
            'article': {
                'headline': 'My Article',
                'reporter': {
                    'id': 1
                }
            }
        },
    }

    schema = graphene.Schema(query=Query, mutation=Mutation)
    result = schema.execute(query)
    assert not result.errors
    assert result.data["createArticle"]["ok"] == expected["createArticle"]["ok"]
    assert all(item in result.data["createArticle"]["article"] for item in expected["createArticle"]["article"])
