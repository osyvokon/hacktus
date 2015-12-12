from flask import Flask
from flask_oauthlib.client import OAuth
import os
import pymongo

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")

app = Flask(__name__)
app.config.from_object('config')

oauth = OAuth(app)
github_auth = oauth.remote_app(
    'github',
    consumer_key=os.environ.get("GITHUB_CLIENT_ID"),
    consumer_secret=os.environ.get("GITHUB_SECRET_ID"),
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)

db = pymongo.Connection().hacktus

from app import views
