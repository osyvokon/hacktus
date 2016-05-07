from flask import Flask
from flask_oauthlib.client import OAuth
from flask.ext.bootstrap import Bootstrap
from celery import Celery
import os
import pymongo

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_SECRET_ID")
GOODREADS_KEY_ID = os.environ.get("GOODREADS_KEY_ID")
GOODREADS_SECRET_ID = os.environ.get("GOODREADS_SECRET_ID")

app = Flask(__name__)
app.config.from_object('config')
bootstrap = Bootstrap(app)

oauth = OAuth(app)
github_auth = oauth.remote_app(
    'github',
    consumer_key=GITHUB_CLIENT_ID,
    consumer_secret=GITHUB_CLIENT_SECRET,
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "hacktus"

def connect_mongo():
    return pymongo.MongoClient(MONGO_URI)[MONGO_DB]

db = connect_mongo()

BROKER_URL = 'redis://localhost:6379/0'
celery = Celery('tasks', broker=BROKER_URL)

from app import views
