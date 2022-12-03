# Ref: https://github.com/miguelgrinberg/Flask-SocketIO/issues/65
from gevent import monkey
monkey.patch_all()

import sys
import os
from flask import Flask, request, jsonify
import logging
import json
from raft.cluster import Cluster
from raft.timer_thread import TimerThread

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

# NODE_ID = int(os.environ.get('NODE_ID'))
# cluster = Cluster()
# node = cluster[NODE_ID]
# timer_thread = TimerThread(NODE_ID)

# def create_app():
#     raft = Flask(__name__)
#     timer_thread.start()
#     return raft

# app = create_app()

app = Flask(__name__)

###### Functions for communication among Server nodes
@app.route('/raft/vote', methods=['POST'])
def request_vote():
    '''
    When a Follower timeout, it becomes a Candidate and starts election by POSTing vote requests to other nodes
    Candidate node -> request_vote() -> Follower nodes
    '''
    candidate_vote_request = request.get_json()
    result = timer_thread.vote(json.loads(candidate_vote_request)) # timer_thread=Follower thread to vote
    return jsonify(result) # return voting result to Candidate

@app.route('/raft/heartbeat', methods=['POST'])
def heartbeat():
    '''
    When a node becomes Leader, it will POST heartbeat requests to other nodes
    Leader node -> heartbeat() -> Follower nodes
    '''
    # leader = request.get_json()
    # logging.info(f'{timer_thread} got heartbeat from Leader: {leader}')
    # response = {"alive": True, "node": node}
    # timer_thread.become_follower() # once receives heartbeat, this node maintains as Follower
    # return jsonify(response)
    
    ## TODO: currently TESTing
    append_entries_request = request.get_json()
    result = timer_thread.append_entries(json.loads(append_entries_request))
    return jsonify(result)

    


# NOTE: TESTING PURPOSE (Delete later)
@app.route('/')
def hello_raft():
    if not_leader():
        return {"result":"Not Leader"}
    else:
        return {"result":"Is Leader!!!"}
    # return f'raft cluster: {cluster}!'


###### Functions for communication between Server and Client
topics = {}

@app.route('/topic', methods=['GET'])
def get_all_topics():
    if not_leader():
        return jsonify({'success': False, 'topics': []})
    
    # TODO NEED TO CHECK GET request string
    # add to Leader's local log
    # client_request = request.get_json()
    # timer_thread.client_append_entries(client_request)

    topic_list = list(topics.keys())
    # print(topic_list)

    statement = {'success': True, 'topics': topic_list}
    return jsonify(statement)
    # if len(topic_list) > 0:
    #     statement = {'success': True, 'topics': topic_list}
    #     return jsonify(statement)
    # else:
    #     statement = {'success': False, 'topics': topic_list}
    #     return jsonify(statement)


@app.route('/topic', methods=['PUT'])
def add_new_topic():
    if not_leader():
        return jsonify({'success': False})

    # TODO
    client_request = request.get_json()
    new_topic = client_request['topic']

    if new_topic in topics:
        return jsonify({'success': False})

    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(client_request))

    # wait until Leader commit confirmed, write to database
    topics[new_topic] = []
    return jsonify({'success': True})

    # NOTE: old
    # new_topic = request.json['topic']
    # if new_topic in topics:
    #     return jsonify({'success': False})
    # topics[new_topic] = []
    # return jsonify({'success': True})


@app.route('/message', methods=['PUT'])
def add_message():
    if not_leader():
        return jsonify({'success': False})
    
    # TODO
    client_request = request.get_json()
    topic = client_request['topic']

    if topic not in topics:
        return jsonify({'success': False})
    
    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(client_request))

    # wait until Leader commit confirmed, write to database
    topics[topic].append(client_request['message'])
    return jsonify({'success': True})

    # NOTE: old
    # topic = request.json['topic']
    # if topic not in topics:
    #     return jsonify({'success': False})
    
    # message = request.json['message']
    # topics[topic].append(message)
    # return jsonify({'success': True})


@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if not_leader():
        # return jsonify({'success': False, 'message': ''})
        return jsonify({'success': False})
    
    if topic not in topics or len(topics[topic]) == 0:
        # return jsonify({'success': False, 'message': ''})
        return jsonify({'success': False})

    # NOTE: 
    # This GET method consumes MQ, 
    # thus considered as WRITE operation and needed to be logged
    client_request = {"topic":topic, "op":"POP"}
    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(client_request))
    message = topics[topic][0]
    topics[topic] = topics[topic][1:]
    return jsonify({'success': True, 'message': message})


    # NOTE: old
    # if topic not in topics or len(topics[topic]) == 0:
    #     return jsonify({'success': False, 'message': ''})
    
    # message = topics[topic][0]
    # topics[topic] = topics[topic][1:]
    # return jsonify({'success': True, 'message': message})


@app.route('/status', methods=['GET'])
def get_status():
    '''
    Return: {'role': <str>, 'term': <int>}
    role options: Leader, Candidate, Follower
    term: the node's current term as an integer
    '''
    node_state = timer_thread.node_state
    role = type(node_state).__name__
    term = node_state.current_term
    response = {'role': role, 'term': term}
    return jsonify(response)

###### Helper functions
def load_conf(filename, node_id, key="addresses"):
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return (config[key], config[key][node_id])
    except FileNotFoundError:
        logging.warning('Config file NOT Found!')

def not_leader():
    role = type(timer_thread.node_state).__name__
    return role != 'Leader'

### python3 src/node.py config.json 0
## app2.py -> node.py
if __name__ == '__main__':
    try:
        json_filename = sys.argv[1].strip()
        node_id = int(sys.argv[2].strip())
        addrs, cur_addr = load_conf(json_filename, node_id)
        # NODE_ID = int(os.environ.get('NODE_ID'))
        cluster = Cluster(addrs)
        node = cluster[node_id]

        # storage_path = './raft/data'
        # if not os.path.exists(storage_path):
        #     os.makedirs(storage_path)

        timer_thread = TimerThread(node_id, cluster)
        # app = create_app()
        timer_thread.start()
        
        # app.run(host=cur_addr['ip'].split("//")[1], port=cur_addr['port'], debug=True)
        # app.run(host=cur_addr['ip'].split("//")[1], port=cur_addr['port'])
        app.run(host=cur_addr['ip'], port=cur_addr['port'])
    except KeyboardInterrupt:
        pass
