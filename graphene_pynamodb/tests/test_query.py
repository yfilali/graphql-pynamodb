import json
import logging

import graphene
from graphene.relay import Node

from .models import Article, Editor, Reporter
from ..fields import PynamoConnectionField
from ..types import PynamoObjectType

logging.basicConfig()


def setup_fixtures():
    for model in [Editor, Article, Reporter]:
        if not model.exists():
            model.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

    reporter = Reporter(id=1, first_name='ABA', last_name='X', awards=['pulizer'],
                        custom_map={'key1': 'value1', 'key2': 'value2'})
    reporter.articles = [Article(1), Article(3)]
    reporter.save()
    reporter2 = Reporter(id=2, first_name='ABO', last_name='Y')
    reporter2.save()
    article1 = Article(id=1, headline='Hi!', reporter=Reporter(1))
    article1.save()
    article2 = Article(id=3, headline='My Article', reporter=Reporter(1))
    article2.save()
    editor = Editor(id='1', name='John')
    editor.save()


setup_fixtures()


def test_should_query_well():
    class ReporterType(PynamoObjectType):
        class Meta:
            model = Reporter

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        reporters = graphene.List(ReporterType)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(1)

        def resolve_reporters(self, *args, **kwargs):
            return list(Reporter.scan())

    query = '''
        query ReporterQuery {
          reporter {
            firstName,
            lastName,
            email,
            customMap,
            awards
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
            'lastName': 'X',
            'customMap': {"key1": "value1", "key2": "value2"},
            'awards': ['pulizer']
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
    result.data['reporter']["customMap"] = json.loads(result.data['reporter']["customMap"])
    assert dict(result.data['reporter']) == expected['reporter']
    assert all(item in result.data['reporters'] for item in expected['reporters'])


def test_should_node():
    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Reporter(id=2, first_name='Cookie Monster')

    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Article(id=1, headline='Article node')

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)
        article = graphene.Field(ArticleNode)
        all_articles = PynamoConnectionField(ArticleNode)

        def resolve_reporter(self, *args):
            return Reporter.get(1)

        def resolve_article(self, *args):
            return Article.get(1)

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
    assert all(item in expected['reporter'] for item in result.data['reporter'])
    assert all(item in expected['reporter']['articles'] for item in result.data['reporter']['articles'])
    assert result.data['myArticle'] == expected['myArticle']
    assert all(item in result.data['allArticles'] for item in expected['allArticles'])


def test_should_custom_identifier():
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
    assert result.data['allEditors'] == expected['allEditors']


def test_should_mutate_well():
    class EditorNode(PynamoObjectType):
        class Meta:
            model = Editor
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
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
        def mutate(cls, root, info, **args):
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
    assert result.data['createArticle']['ok'] == expected['createArticle']['ok']
    assert all(item in result.data['createArticle']['article'] for item in expected['createArticle']['article'])


def test_should_return_empty_cursors_on_empty():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(2)

    query = '''
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles(first: 1) {
              edges {
                node {
                  id
                  headline
                }
              }
              pageInfo {
                hasNextPage
                hasPreviousPage
                startCursor
                endCursor
              }
            }
            lastName,
            email
          }
        }
    '''
    expected = {
        'reporter': {
            'articles': {
                'edges': [],
                'pageInfo': {
                    'hasNextPage': False,
                    'hasPreviousPage': False,
                    'startCursor': '',
                    'endCursor': ''
                }
            }
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter']['articles']['edges'] == expected['reporter']['articles']['edges']
    assert result.data['reporter']['articles']['pageInfo'] == expected['reporter']['articles']['pageInfo']


def test_should_support_first():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(1)

    query = '''
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles(first: 1) {
              edges {
                node {
                  id
                  headline
                }
              }
              pageInfo {
                hasNextPage
                hasPreviousPage
                startCursor
                endCursor
              }
            }
            lastName,
            email
          }
        }
    '''
    expected = {
        'reporter': {
            'articles': {
                'edges': [{
                    'node': {
                        'id': 'QXJ0aWNsZU5vZGU6MQ==',
                        'headline': 'Hi!'
                    }
                }],
                'pageInfo': {
                    'hasNextPage': True,
                    'hasPreviousPage': False,
                    'startCursor': '1',
                    'endCursor': '1'
                }
            }
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter']['articles']['edges'] == expected['reporter']['articles']['edges']
    assert result.data['reporter']['articles']['pageInfo'] == expected['reporter']['articles']['pageInfo']


def test_should_support_last():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(1)

    query = '''
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles(last: 1) {
              edges {
                node {
                  id
                  headline
                }
              }
            }
            lastName,
            email
          }
        }
    '''
    expected = {
        'reporter': {
            'articles': {
                'edges': [{
                    'node': {
                        'id': 'QXJ0aWNsZU5vZGU6Mw==',
                        'headline': 'My Article'
                    }
                }]
            }
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter']['articles']['edges'] == expected['reporter']['articles']['edges']


def test_should_support_after():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(1)

    query = '''
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles(after: "QXJ0aWNsZU5vZGU6MQ==") {
              edges {
                node {
                  id
                  headline
                }
              }
            }
            lastName,
            email
          }
        }
    '''
    expected = {
        'reporter': {
            'articles': {
                'edges': [{
                    'node': {
                        'id': 'QXJ0aWNsZU5vZGU6Mw==',
                        'headline': 'My Article'
                    }
                }]
            }
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['reporter']['articles']['edges'] == expected['reporter']['articles']['edges']


def test_root_scan_should_warn_on_params():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = PynamoConnectionField(ArticleNode)

    query = '''
        query ArticlesQuery {
          articles(after: "QXJ0aWNsZU5vZGU6MQ==") {
            edges {
              node {
                id
                headline
              }
            }
          }
        }
    '''

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert result.errors
    assert isinstance(result.errors[0].original_error, NotImplementedError)


def test_root_scan_should_fastforward_on_after():
    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        node = Node.Field()
        articles = PynamoConnectionField(ArticleNode)

        def resolve_articles(self, *args, **kwargs):
            return [
                Article(1, headline='One'),
                Article(2, headline='Two'),
                Article(3, headline='Three'),
                Article(4, headline='Four')
            ]

    query = '''
        query ArticlesQuery {
          articles(after: "QXJ0aWNsZU5vZGU6Mq==", first: 1) {
            edges {
              node {
                id
                headline
              }
            }
          }
        }
    '''
    expected = [{
        'node': {
            'headline': 'Three',
            'id': 'QXJ0aWNsZU5vZGU6Mw=='
        }
    }]

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data['articles']['edges'] == expected


def test_should_return_total_count():
    class ReporterNode(PynamoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Reporter(id=2, first_name='Cookie Monster')

    class ArticleNode(PynamoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Article(id=1, headline='Article node')

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)
        article = graphene.Field(ArticleNode)
        all_articles = PynamoConnectionField(ArticleNode)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.get(1)

        def resolve_article(self, *args, **kwargs):
            return Article.get(1)

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
    assert all(item in expected['reporter'] for item in result.data['reporter'])
    assert all(item in expected['reporter']['articles'] for item in result.data['reporter']['articles'])
    assert result.data['myArticle'] == expected['myArticle']
    assert all(item in result.data['allArticles'] for item in expected['allArticles'])
