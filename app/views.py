from app import app, github_auth, db
from flask import render_template, flash, redirect, request, g, session, url_for, jsonify
from app.github_task import GithubProvider, get_stats_for_day
from app.codeforces_task import CodeforcesProvider, get_stats_for_day as codeforces_stats
from forms import SettingsForm
import datetime


@app.before_request
def before_request():
    g.user = None

@app.route('/')
@app.route('/index')
def index():
    if 'github_token' in session:
        user = github_auth.get('user')
        return jsonify(user.data)
    else:
        user = None
    return render_template('index.html',
                           title='Home',
                           user=user)

@app.route('/gh_callback')
def authorized():
    resp = github_auth.authorized_response()
    if resp is None:
        return 'Access denied'
    session['github_token'] = (resp['access_token'], '')
    user = github_auth.get('user')
    print("Authorized GitHub, token is {}".format(resp['access_token']))
    return jsonify(user.data)

@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github_auth.authorize(
                callback=url_for('authorized', _external=True))
    else:
        return "Already logged in"

@github_auth.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.route('/stats')
def stats():
    token = get_github_oauth_token()[0]
    result = []
    now = datetime.date.today().toordinal()
    for x in range(7):
        dt = now - x
        stats = db.github.by_day.find_one({'dt': dt})
        if stats:
            stats = stats['stats']
        else:
            stats = {"msg": "IN PROGRESS"}
            get_stats_for_day.delay(token, datetime.datetime.fromordinal(dt))
        result.append(stats)
    return jsonify({'result': result})

@app.route('/cf_stats')
def cf_stats():
    result = []
    now = datetime.date.today().toordinal()
    for x in range(30):
        dt = now - x
        stats = db.codeforces.by_day.find_one({'dt': dt})
        if stats:
            stats = stats['stats']
        else:
            stats = {"msg": "IN PROGRESS"}
            codeforces_stats.delay(datetime.datetime.fromordinal(dt))
        result.append(stats)
    return jsonify({'result': result})

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        flash('Settings saved!')
        session['cf_login'] = form.cf_login.data
    else:
        if 'cf_login' in session:
            form.cf_login.data = session['cf_login']
    return render_template('settings.html', form=form, title='Settings')

@app.route('/codeforces')
def codeforces():
    now = datetime.date.today()
    return jsonify(codeforces_stats(now))
