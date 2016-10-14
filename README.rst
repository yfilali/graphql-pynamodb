Please read
`UPGRADE-v1.0.md <https://github.com/graphql-python/graphene/blob/master/UPGRADE-v1.0.md>`__
to learn how to upgrade to Graphene ``1.0``.

--------------

|Graphene Logo| Graphene-PynamoDB |Build Status| |Coverage Status|
==================================================================

A `PynamoDB <http://pynamodb.readthedocs.io/>`__ integration for
`Graphene <http://graphene-python.org/>`__.

Installation
------------

For instaling graphene, just run this command in your shell

.. code:: bash

    pip install git+git://github.com/yfilali/graphql-pynamodb

Examples
--------

Here is a simple PynamoDB model:

.. code:: python

    from uuid import uuid4
    from pynamodb.attributes import UnicodeAttribute
    from pynamodb.models import Model


    class User(Model):
        class Meta:
            table_name = "my_users"
            host = "http://localhost:8000"

        id = UnicodeAttribute(hash_key=True)
        name = UnicodeAttribute(null=False)


    if not User.exists():
        User.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
        User(id=str(uuid4()), name="John Snow").save()
        User(id=str(uuid4()), name="Daenerys Targaryen").save()

To create a GraphQL schema for it you simply have to write the
following:

.. code:: python

    import graphene
    from graphene_pynamodb import PynamoObjectType


    class UserNode(PynamoObjectType):
        class Meta:
            model = User
            interfaces = (graphene.Node,)


    class Query(graphene.ObjectType):
        users = graphene.List(UserNode)

        def resolve_users(self, args, context, info):
            return User.scan()


    schema = graphene.Schema(query=Query)

Then you can simply query the schema:

.. code:: python

    query = '''
        query {
          users {
            name
          }
        }
    '''
    result = schema.execute(query)

To learn more check out the following `examples <examples/>`__:

-  **Full example**: `Flask PynamoDB
   example <examples/flask_pynamodb>`__

Contributing
------------

After cloning this repo, ensure dependencies are installed by running:

.. code:: sh

    python setup.py install

After developing, the full test suite can be evaluated by running:

.. code:: sh

    python setup.py test # Use --pytest-args="-v -s" for verbose mode

.. |Graphene Logo| image:: http://graphene-python.org/favicon.png
.. |Build Status| image:: https://travis-ci.org/yfilali/graphql-pynamodb.svg?branch=master
   :target: https://travis-ci.org/yfilali/graphql-pynamodb
.. |Coverage Status| image:: https://coveralls.io/repos/github/yfilali/graphql-pynamodb/badge.svg?branch=master
   :target: https://coveralls.io/github/yfilali/graphql-pynamodb?branch=master
