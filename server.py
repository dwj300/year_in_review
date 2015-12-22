from flask import Flask, flash, render_template, request, redirect, url_for
from flask import session
from flask.ext.github import GitHub

app = Flask(__name__)
app.config['GITHUB_CLIENT_ID'] = '23f6a7ed58a974ed0ebc'
app.config['GITHUB_CLIENT_SECRET'] = 'f619bf337176c0adf443f37a298663ba2c9d8843'
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/RTRT'
github = GitHub(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return github.authorize()

@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect(url_for('index')


@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect(next_url)
    session['token'] = oauth_token

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
