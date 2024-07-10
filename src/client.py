import requests
import json
import sys
import threading

headers = {"Content-Type": "application/json"}

def create_topic(url, topic, endpoint='topic'):

    body = {'topic': topic}
    response = requests.put(
        f'{url}/{endpoint}',
        data=json.dumps(body),
        headers=headers
    )

    # Testing
    print('raw response',response)
    print('json response',response.json())

    res = response.json()
    if res['success']:
        print('New Topic Successfully Created!')
    else:
        print('Failed To Create New Topic')

def get_topics(url, endpoint='topic'):
    response = requests.get(f'{url}/{endpoint}') 

    # Testing
    print('raw response',response)
    print('json response',response.json())

    res = response.json()
    if res['success']:
        print('Topics Successfully Retrieved: ', res['topics'])
    else:
        print('Failed To Retrieve Topics')


def add_message(url, topic, message, endpoint='message'):
    body = {'topic': topic, 'message': message}

    response = requests.put(
        f'{url}/{endpoint}',
        data=json.dumps(body),
        headers=headers
    )
    
    # Testing
    print('raw response',response)
    print('json response',response.json())

    res = response.json()
    if res['success']:
        print('New Message Successfully Added!')
    else:
        print('Failed To Add New Message')

def get_message(url, topic, endpoint='message'):
    response = requests.get(f'{url}/{endpoint}/{topic}')

    # Testing
    print('raw response', response)
    print('json response', response.json())

    res = response.json()
    if res['success']:
        print('Message Successfully Retrieved: ', res['message'])
    else:
        print('Failed To Retrieve Message')


def get_status(url, endpoint='status'):
    response = requests.get(f'{url}/{endpoint}')
    # Testing
    print('raw response', response)
    print('json response', response.json())


def hello_raft(url):
    response = requests.get(f'{url}')
    print('json response', response.json())


IP = '127.0.0.1'
if __name__ == '__main__':
    try:
        port = int(sys.argv[1].strip())
        url = f'http://{IP}:{port}'

        create_topic(url, topic="math")
        print('-------------------')

        get_topics(url)
        print('-------------------')

        add_message(url, topic="math", message='hello')
        print('-------------------')

        add_message(url, topic="math", message='world')
        print('-------------------')

        get_message(url, topic="math")
        print('-------------------')

        get_message(url, topic="math")
        print('-------------------')

        get_message(url, topic="math")
        print('-------------------')

        ## TEST Election Algorithm
        get_status(url)
        # hello_raft(url)
        
        
    except KeyboardInterrupt:
        pass