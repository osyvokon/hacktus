from app import app
from .forms import LoginForm
from flask import render_template, flash, redirect
import requests
import json

GITHUB_API = 'https://api.github.com'
gh = {
    'login': None,
    'password': None
}

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Marina'}  # fake user
    return render_template('index.html',
                           title='Home',
                           user=user)

@app.route('/signin')
def signin():
    url = GITHUB_API + '/authorizations'
    payload = {
        'note': 'temporary auth'
    }
    res = requests.post(
        url,
        auth = (gh['login'], gh['password']),
        data = json.dumps(payload),
    )
    return res.text
    # return render_template('signin.html',
    #                        title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        gh['login'] = form.gh_login.data
        gh['password'] = form.gh_password.data
        flash('Login requested for GitHub="%s", remember_me=%s' %
              (form.gh_login.data, str(form.remember_me.data)))
        return redirect('/signin')
    return render_template('login.html',
                           title='Sign In',
                           form=form)
