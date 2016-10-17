PynamoDB + Flask Tutorial
=========================

To use graphene with pynamodb, you need to install the graphene-pynamodb from pypi:
.. code:: bash
pip install graphene-pynamodb

Note: The code in this tutorial is pulled from the `Flask PynamoDB
example
app <https://github.com/yfilali/graphql-pynamodb/tree/master/examples/flask_pynamodb>`__.

Setup the Project
-----------------

We will setup the project, execute the following:

.. code:: bash

    # Create the project directory
    mkdir flask_pynamodb
    cd flask_pynamodb

    # Create a virtualenv to isolate our package dependencies locally
    virtualenv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`

    # Install graphene with pynamodb support
    pip install graphene-pynamodb

    # Install Flask and GraphQL Flask for exposing the schema through HTTP
    pip install Flask
    pip install Flask-GraphQL

Defining our models
-------------------

Let's get started with these models:

.. code:: python
from datetime import datetime
    from graphene_pynamodb.relationships import OneToOne
    from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
    from pynamodb.models import Model


    class Department(Model):
        class Meta:
            table_name = 'flask_pynamodb_example_department'
            host = "http://localhost:8000"

        id = UnicodeAttribute(hash_key=True)
        name = UnicodeAttribute()


    class Role(Model):
        class Meta:
            table_name = 'flask_pynamodb_example_roles'
            host = "http://localhost:8000"

        id = UnicodeAttribute(hash_key=True)
        name = UnicodeAttribute()


    class Employee(Model):
        class Meta:
            table_name = 'flask_pynamodb_example_employee'
            host = "http://localhost:8000"

        id = UnicodeAttribute(hash_key=True)
        name = UnicodeAttribute()
        hired_on = UTCDateTimeAttribute(default=datetime.now)
        department = OneToOne(Department)
        role = OneToOne(Role)

Schema
------

GraphQL presents your objects to the world as a graph structure rather
than a more hierarchical structure to which you may be accustomed. In
order to create this representation, Graphene needs to know about each
*type* of object which will appear in the graph.

This graph also has a *root type* through which all access begins. This
is the ``Query`` class below. In this example, we provide the ability to
list all employees via ``all_employees``, and the ability to obtain a
specific node via ``node``.

Create ``flask_pynamodb/schema.py`` and type the following:

.. code:: python

    # flask_pynamodb/schema.py
    import graphene
    from graphene import relay
    from graphene_pynamodb import PynamoConnectionField, PynamoObjectType
    from models import Department as DepartmentModel
    from models import Employee as EmployeeModel
    from models import Role as RoleModel


    class Department(PynamoObjectType):
        class Meta:
            model = DepartmentModel
            interfaces = (relay.Node,)


    class Employee(PynamoObjectType):
        class Meta:
            model = EmployeeModel
            interfaces = (relay.Node,)


    class Role(PynamoObjectType):

        class Meta:
            model = RoleModel
            interfaces = (relay.Node,)


    class Query(graphene.ObjectType):
        node = relay.Node.Field()
        all_employees = PynamoConnectionField(Employee)
        all_roles = PynamoConnectionField(Role)
        role = graphene.Field(Role)


    schema = graphene.Schema(query=Query, types=[Department, Employee, Role])


Creating GraphQL and GraphiQL views in Flask
--------------------------------------------

Unlike a RESTful API, there is only a single URL from which GraphQL is
accessed.

We are going to use Flask to create a server that expose the GraphQL
schema under ``/graphql`` and a interface for querying it easily:
GraphiQL (also under ``/graphql`` when accessed by a browser).

Fortunately for us, the library ``Flask-GraphQL`` that we previously
installed makes this task quite easy.

.. code:: python

    # flask_pynamodb/app.py
    from flask import Flask
    from flask_graphql import GraphQLView

    from models import db_session
    from schema import schema, Department

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
    )

    if __name__ == '__main__':
        app.run()

Creating some data
------------------

.. code:: python

    # flask_pynamodb/database.py

    def init_db():
        from models import Department, Employee, Role
        for model in [Department, Employee, Role]:
            if model.exists():
                model.delete_table()
            model.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

        # Create the fixtures
        engineering = Department(id=str(uuid4()), name='Engineering')
        engineering.save()
        hr = Department(id=str(uuid4()), name='Human Resources')
        hr.save()

        manager = Role(id=str(uuid4()), name='manager')
        manager.save()

        engineer = Role(id=str(uuid4()), name='engineer')
        engineer.save()

        peter = Employee(id=str(uuid4()), name='Peter', department=engineering, role=engineer)
        peter.save()

        roy = Employee(id=str(uuid4()), name='Roy', department=engineering, role=engineer)
        roy.save()

        tracy = Employee(id=str(uuid4()), name='Tracy', department=hr, role=manager)
        tracy.save()

.. code-block:: bash
    $ python
    >>> from database import init_db
    >>> init_db()

Testing our GraphQL schema
--------------------------

We're now ready to test the API we've built. Let's fire up the server
from the command line.

.. code:: bash

    $ python ./app.py

     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Go to `localhost:5000/graphql <http://localhost:5000/graphql>`__ and
type your first query!

.. code::

    {
      allEmployees {
        edges {
          node {
            id
            name
            department {
              name
            }
          }
        }
      }
    }
