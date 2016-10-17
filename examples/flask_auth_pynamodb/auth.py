from flask import g
 
from models import User
 
 
def authenticate(email, password):
    try:
        user = User.email_index.query(email).next()
    except StopIteration:
        return None
 
    if user and user.check_password(password):
        return user
 
 
def identity(payload):
    user_id = payload['identity']
    try:
        g.user = User.get(user_id, None)
        return g.user
    except User.DoesNotExist:
        return None
