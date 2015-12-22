from flask import Flask, flash, render_template, request, redirect, url_for
from flask import session
from flask.ext.github import GitHub, GitHubError
# ToDo: Before going public make sure to make these environemnt variables...
app = Flask(__name__)
app.config['GITHUB_CLIENT_ID'] = '2be5054af9310faa5019'
app.config['GITHUB_CLIENT_SECRET'] = 'e6cee1a10872488d875f9408432be467cb40ea22'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/RTRT'
github = GitHub(app)


@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=username, name=name)
    else:
        return render_template('index.html')


@app.route('/login')
def login():
    return github.authorize(scope="repo:status")


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
    next_url = request.args.get('next') or url_for('index')
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
    username = request.args.get('username', '')
    print(username)
    return render_template('review.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)
