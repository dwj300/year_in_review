from flask import Flask, flash, render_template, request, redirect, url_for
from flask import session
from flask.ext.github import GitHub, GitHubError
import os
import json
import pika
from azure.storage.blob import BlobService

# todo: cleanup before posting on HackerNews and becoming famous
# todo: make it look like legit.
# todo: DO NOT FORGET GOOGLE HIT COUNTER
# todo: add delete option...
# todo: add warnign about private info
# todo: add robots

app = Flask(__name__)
app.config['GITHUB_CLIENT_ID'] = os.environ['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = os.environ['GITHUB_CLIENT_SECRET']
app.secret_key = os.environ['SECRET_KEY']
github = GitHub(app)

# Queue stuff
url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost/%2f')
params = pika.URLParameters(url)
params.socket_timeout = 5
connection = pika.BlockingConnection(params)  # Connect to CloudAMQP
channel = connection.channel()  # start a channel
channel.queue_declare(queue='work')  # Declare a queue

# Azure storage
account_name = os.environ.get('AZURE_NAME', '')
account_key = os.environ.get('AZURE_KEY', '')
blob_service = BlobService(account_name, account_key)


@app.route('/')
def index():
    print("foo")
    if 'username' in session:
        return render_template('index.html',
                               username=session['username'],
                               name=session['name'])
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


@app.route('/delete')
def delete():
    if 'username' in session:
        username = session['username']
        blob_service.delete_blob('static', username+".html")
    return redirect(url_for('index'))


@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    # next_url = url_for('review')
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
    return redirect(next_url)


@github.access_token_getter
def token_getter():
    if 'token' in session:
        return session['token']


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


@app.route('/review/<public_str>')
def review(public_str):
    public = str2bool(public_str)
    token = session['token']
    username = session['username']
    name = session['name']

    data = {'token': token, 'username': username,
            'name': name, 'public': public}
    channel.basic_publish(exchange='',
                          routing_key='work',
                          body=json.dumps(data))
    print(" [x] Sent" + json.dumps(data))
    resp = render_template('wait.html', username=session['username'])
    return resp
    # ToDo: deal with private!
    # ToDo: also filter by org or nah
    # maybe move to new method, or even class


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
