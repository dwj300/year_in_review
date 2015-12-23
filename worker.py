import logging
import os
import pika
import json
logging.basicConfig()

url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost/%2f')

# Parse CLODUAMQP_URL (fallback to localhost)
url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost/%2f')
params = pika.URLParameters(url)
params.socket_timeout = 5
connection = pika.BlockingConnection(params)  # Connect to CloudAMQP
channel = connection.channel()   # start a channel
channel.queue_declare(queue='work')  # Declare a queue
# send a message
#channel.basic_publish(exchange='', routing_key='hello', body='Hello CloudAMQP!')
#print " [x] Sent 'Hello World!'"


# create a function which is called on incoming messages
def do_work(ch, method, properties, body):
    print("[x] Received {0}".format(body))
    data = json.loads(body)
    print(data.token)
    print(data.username)


def setup():
    # set up subscription on the queue
    channel.basic_consume(do_work, queue='work', no_ack=True)
    channel.start_consuming()  # start consuming (blocks)
    connection.close()

if __name__ == '__main__':
    setup()
