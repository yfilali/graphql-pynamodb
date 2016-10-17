Example Flask+PynamoDB Project
================================

This example project demos integration between Graphene, Flask, 
Flask-JWT and PynamoDB.
The project a User model, an authenticated graphql endpoint, and some 
basic security around getting user objects through graphql.

Getting started
---------------

First you'll need to get the source of the project. Do this by cloning the
whole repository:

```bash
# Get the example project code
git clone https://github.com/yfilali/graphql-pynamodb.git
cd graphql-pynamodb/examples/flask_auth_pynamodb
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
python ./run.py
```

Create a user in the database:
```
$ python
>>> from models import User
>>> user = User(email="you@email.com", first_name="Me", last_name="Myself")
>>> user.password = "yourpass"
>>> user.save()
```

Then get your JWT access token:

```
curl -X POST -H "Content-Type: application/json" -d '{"email":"you@email.com","password":"yourpass"}' "http://127.0.0.1:5000/login"
```

Now head on over to
[http://127.0.0.1:5000/graphql](http://127.0.0.1:5000/graphql)
and run some queries! You'll need a browser extension like ModHeaders to pass an Authorization header with your JWT token:
Authorization: JWT token-goes-here

You can also test it using curl:
```
curl -X GET -H "Authorization: JWT [token from previous curl request]" "http://127.0.0.1:5000/graphql?query=\{viewer\{id,firstName,lastName,email\}\}"
```

Here is a simple GraphQL query to get you started:
```
{
  viewer {
    firstName
    lastName
    email
  }
}

```