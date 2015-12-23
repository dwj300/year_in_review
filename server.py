from flask import Flask, flash, render_template, request, redirect, url_for
from flask import session
from flask.ext.github import GitHub, GitHubError
from github import Github
from datetime import datetime
from collections import namedtuple
# ToDo: Before going public make sure to make these environemnt variables...
# ToDo: cleanup before posting on HackerNews and becoming famous
# ToDo: make it look like legit.
# ToDo: DO NOT FORGET GOOGLE HIT COUNTER

app = Flask(__name__)
app.config['GITHUB_CLIENT_ID'] = '2be5054af9310faa5019'
app.config['GITHUB_CLIENT_SECRET'] = 'e6cee1a10872488d875f9408432be467cb40ea22'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/RTRT'
github = GitHub(app)


@app.route('/')
def index():
    print("foo")
    if 'username' in session:
        return render_template('index.html', username=session['username'], name=session['name'])
    else:
        return render_template('index.html')


@app.route('/login')
def login():
    return github.authorize(scope="repo")


@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('github_user_id', None)
    session.pop('username', None)
    session.pop('name', None)
    session.pop('avatar_url', None)
    return redirect(url_for('index'))


@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    # next_url = request.args.get('next') or url_for('index')
    next_url = url_for('review')
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect(next_url)
    session['token'] = oauth_token
    try:
        response = github.get('user', params={'access_token': oauth_token})
    except GitHubError:
        flash(
            'something failed in github login process, sorry for that',
            category='danger'
        )
        return redirect(url_for('index.index'))

    session['github_user_id'] = response['id']
    session['username'] = response['login']
    session['name'] = response['name']
    session['avatar_url'] = response['avatar_url']
    session['user'] = response
    """user = User.query.filter_by(github_access_token=oauth_token).first()
    if user is None:
        user = User(oauth_token)
        db_session.add(user)

    user.github_access_token = oauth_token
    db_session.commit()"""
    return redirect(next_url)


@github.access_token_getter
def token_getter():
    if 'token' in session:
        return session['token']


@app.route('/review')
def review():
    # ToDo: deal with private!
    # ToDo: also filter by org or nah
    # maybe move to new method, or even class
    private = True
    """print(session['user'].keys())
    user = session['user']"""
    token = session['token']
    # repos_url = user['repos_url']
    # print(repos_url)
    print(token)
    start = datetime(2015, 1, 1)  # make global?
    # repos = github.get('user/repos', params={'type': 'all', 'access_token': token})
    # print(len(repos))
    gh = Github(token)
    user = gh.get_user()
    repos = user.get_repos()
    my_repos = []
    for repo in repos:
        my_repo = namedtuple('Repo', ['name', 'num_commits'])
        print(repo.name)
        my_repo.name = repo.name
        commits = repo.get_commits(author=user, since=start)
        my_commits = []
        for commit in commits:
            my_commits.append(commit)
        print(len(my_commits))
        my_repo.num_commits = len(my_commits) 
        if my_repo.num_commits > 0:
            my_repos.append(my_repo)
    my_repos.sort(key=lambda x: x.num_commits, reverse=True)
    total = sum(r.num_commits for r in my_repos)
    return render_template('review.html',
                           username=session['username'],
                           name=session['name'],
                           repos=my_repos,
                           total=total)

if __name__ == '__main__':
    app.run(debug=True)
