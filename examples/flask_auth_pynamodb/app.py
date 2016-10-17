import os
from datetime import timedelta
 
from flask import Flask
from flask_cors import CORS
from flask_jwt import JWT
 
from auth import identity, authenticate
 
app = Flask(__name__)
app.config["DEBUG"] = os.environ.get("DEBUG", True)
app.config["JWT_AUTH_USERNAME_KEY"] = "email"
app.config["JWT_EXPIRATION_DELTA"] = timedelta(7 * 24 * 60 * 60)
app.config["JWT_AUTH_URL_RULE"] = "/login"
app.config["SECRET_KEY"] = "Super duper secret"
 
CORS(app)
jwt = JWT(app, authenticate, identity)
