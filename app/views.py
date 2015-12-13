from app import app, github_auth, db
from flask import render_template, flash, redirect, request, g, session, url_for, jsonify
from app.github_task import GithubProvider, get_github_stats_for_day
from app.codeforces_task import CodeforcesProvider
from app.forms import SettingsForm
import datetime
from collections import Counter

@app.before_request
def before_request():
    g.user = None

@app.route('/')
@app.route('/index')
def index():
    if 'github_token' in session:
        return redirect(url_for('profile'))
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
    session['user'] = user.data
    print("Authorized GitHub, token is {}".format(resp['access_token']))
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    return render_template('profile.html',
                           title='Profile',
                           user=user,
                           scores=get_scores(user),
                           hacktivities=map(format_day, _stats()))

def format_day(day):
    if day.get('msg') == "IN PROGRESS":
        return "...collecting data, please wait"

    else:
        s = []
        for k, v in sorted(day.items()):
            if v:
                s.append('{k} = {v}'.format(k=k, v=v))
        return '; '.join(s)



@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github_auth.authorize(
                callback=url_for('authorized', _external=True))
    else:
        return "Already logged in"


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@github_auth.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.route('/stats')
def stats():
    return jsonify({'result': _stats()})

def _stats():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    name = user['login']
    if not name:
        return redirect(url_for('login'))

    token = get_github_oauth_token()[0]
    result = []
    now = datetime.date.today().toordinal()
    for x in range(5):
        dt = now - x
        stats = db.github.by_day.find_one({'user': name, 'dt': dt})
        if stats:
            stats = stats['stats']
        else:
            stats = {"msg": "IN PROGRESS"}
            get_github_stats_for_day.delay(token, datetime.datetime.fromordinal(dt), name)
        result.append(stats)
    return result

@app.route('/cf_stats')
def cf_stats():
    if 'cf_login' not in session:
        return redirect(url_for(settings))

    result = {}
    name = session['cf_login']
    provider = CodeforcesProvider(name)
    now = datetime.date.today()
    result['daily'] = provider.get_stats_for_day(name, now)
    result['weekly'] = provider.get_stats_for_week(name)
    result['monthly'] = provider.get_stats_for_month(name)
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
    if 'cf_login' not in session:
        return redirect(url_for(settings))

    today = datetime.date.today()
    pr = CodeforcesProvider(session['cf_login'])
    return jsonify(pr.get_submissions(today))

def get_scores(user):
    scores = Counter()
    for x in db.github.by_day.find():     # filter by user
        stats = x.get('stats') 
        if not stats:
            continue
        scores.update(stats)

        # do not sum repos_count, rather use latest value
        # (FIXME which is currently random)
        if 'repos_count' in stats:
            scores['repos_count'] = stats['repos_count']
        if 'stars' in stats:
            scores['stars'] = stats['stars']

    scores['level'] = int(scores['stars'] / 10 +
                          scores['additions'] / 500 +
                          scores['repos_count'] / 5)

    return scores

