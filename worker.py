import logging
import os
import pika
import json
from datetime import datetime
from github import Github
from collections import namedtuple
from flask import render_template
from server import app
from azure.storage.blob import BlobService

logging.basicConfig()

url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost/%2f')

# Parse CLODUAMQP_URL (fallback to localhost)
url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost/%2f')
params = pika.URLParameters(url)
params.socket_timeout = 5
connection = pika.BlockingConnection(params)  # Connect to CloudAMQP
channel = connection.channel()   # start a channel
channel.queue_declare(queue='work')  # Declare a queue
SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:5000')
app.config['SERVER_NAME'] = SERVER_NAME

account_name = os.environ.get('AZURE_NAME', '')
account_key = os.environ.get('AZURE_KEY', '')

blob_service = BlobService(account_name, account_key)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# create a function which is called on incoming messages
def do_work(ch, method, properties, body):
    print("[x] Received {0}".format(body))
    data = json.loads(body.decode("utf-8"))
    print(data['token'])
    print(data['username'])
    # ToDo: deal with private!
    # ToDo: also filter by org or nah
    # maybe move to new method, or even class
    private = True
    # token = session['token']
    token = data['token']
    username = data['username']
    # repos_url = user['repos_url']
    # print(repos_url)
    print(token)
    days = [0 for _ in range(7)]
    start = datetime(2015, 1, 1)  # make global?
    gh = Github(token)
    user = gh.get_user()
    repos = user.get_repos()
    my_repos = []
    add = 0
    dele = 0
    for repo in repos:
        my_repo = namedtuple('Repo', ['name', 'num_commits'])
        print(repo.name)
        my_repo.name = repo.name
        try:
            commits = repo.get_commits(author=user, since=start)
            my_commits = []
            for commit in commits:
                my_commits.append(commit)
                stats = commit.stats
                add += stats.additions
                dele += stats.deletions
                # 0 is monday
                day = commit.commit.author.date.weekday()
                days[day] += 1
            print(len(my_commits))
            my_repo.num_commits = len(my_commits)
            if my_repo.num_commits > 0:
                my_repos.append(my_repo)
        except:
            pass
    my_repos.sort(key=lambda x: x.num_commits, reverse=True)
    total = sum(r.num_commits for r in my_repos)
    best_day_num = max(days)
    best_day = days.index(best_day_num)
    with app.app_context():
        resp = render_template('review.html',
                               username=username,
                               repos=my_repos,
                               total=total,
                               add='{0:,}'.format(add),
                               dele='{0:,}'.format(dele),
                               days=days,
                               best_day_num=best_day_num,
                               best_day=DAYS[best_day])
    print("hmm")
    # f = open('static/'+username+".html", 'w+')
    print("hmm1")
    # f.write(resp)
    # f.close()
    blob_service.put_blob('static', username+".html", resp.encode(),  x_ms_blob_type='BlockBlob', x_ms_blob_content_type="text/html")
    print("done with " + username)

def setup():
    # set up subscription on the queue
    print("starting worker")
    channel.basic_consume(do_work, queue='work', no_ack=True)
    channel.start_consuming()  # start consuming (blocks)
    connection.close()

if __name__ == '__main__':
    setup()
    print("worker exiting...")
