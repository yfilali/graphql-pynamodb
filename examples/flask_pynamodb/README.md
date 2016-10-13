Example Flask+PynamoDB Project
================================

This example project demos integration between Graphene, Flask and PynamoDB.
The project contains two models, one named `Department` and another
named `Employee`.

Getting started
---------------

First you'll need to get the source of the project. Do this by cloning the
whole repository:

```bash
# Get the example project code
git clone https://github.com/yfilali/graphql-pynamodb.git
cd graphql-pynamodb/examples/flask_pynamodb
```

It is good idea (but not required) to create a virtual environment
for this project. We'll do this using
[virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
to keep things simple,
but you may also find something like
[virtualenvwrapper](https://virtualenvwrapper.readthedocs.org/en/latest/)
to be useful:

```bash
# Create a virtualenv in which we can install the dependencies
virtualenv env
source env/bin/activate
```

Now we can install our dependencies:

```bash
pip install -r requirements.txt
```

**IMPORTANT**

The example assumes a local dynamodb database. [You can get it here](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
Alternatively, you can run against aws dynamodb by setting your aws credentials using 'aws configure'  

Now the following command will setup the database, and start the server:

```bash
./app.py

```


Now head on over to
[http://127.0.0.1:5000/graphql](http://127.0.0.1:5000/graphql)
and run some queries!

Here is one to get you started:
```
{
  allEmployees {
    edges {
      node {
        id
        name
        department {
          id
          name
        }
        role {
          name
        }
        hiredOn
      }
    }
  }
}

```