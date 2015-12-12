from app import app, github, db
from flask import render_template, flash, redirect, request, g, session, url_for, jsonify
import requests
import json


@app.before_request
def before_request():
    g.user = None

@app.route('/')
@app.route('/index')
def index():
    if 'github_token' in session:
        user = github.get('user')
    else:
        user = None
    return render_template('index.html',
                           title='Home',
                           user=user)

@app.route('/gh_callback')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        return 'Access denied'
    session['github_token'] = (resp['access_token'], '')
    user = github.get('user')
    return jsonify(user.data)

@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize(
                callback=url_for('authorized', _external=True))
    else:
        return "Already logged in"

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')
