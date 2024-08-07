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
    append_entries_request = request.get_json()
    result = timer_thread.append_entries(json.loads(append_entries_request))
    return jsonify(result)



###### Functions for communication between Server and Client
@app.route('/topic', methods=['GET'])
def get_all_topics():
    if not_leader():
        return jsonify({'success': False, 'topics': []})
    
    topics = json.loads(timer_thread.fetch_MQ())

    topic_list = list(topics.keys())

    statement = {'success': True, 'topics': topic_list}
    return jsonify(statement)


@app.route('/topic', methods=['PUT'])
def add_new_topic():
    if not_leader():
        return jsonify({'success': False})

    topics = json.loads(timer_thread.fetch_MQ())

    client_request = request.get_json()
    new_topic = client_request['topic']

    if new_topic in topics:
        return jsonify({'success': False})
    
    topics[new_topic] = []
    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(topics))
    return jsonify({'success': True})


@app.route('/message', methods=['PUT'])
def add_message():
    if not_leader():
        return jsonify({'success': False})

    topics = json.loads(timer_thread.fetch_MQ())

    client_request = request.get_json()
    topic = client_request['topic']

    if topic not in topics:
        return jsonify({'success': False})
    
    topics[topic].append(client_request['message'])

    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(topics))
    return jsonify({'success': True})



@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if not_leader():
        return jsonify({'success': False})

    topics = json.loads(timer_thread.fetch_MQ())

    if topic not in topics or len(topics[topic]) == 0:
        return jsonify({'success': False})
    
    message = topics[topic][0]
    topics[topic] = topics[topic][1:]
    # add to Leader's local log
    timer_thread.client_append_entries(json.dumps(topics))
    return jsonify({'success': True, 'message': message})
    


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


## node.py: Receives RPC from client.py
### > python3 src/node.py config.json 0
if __name__ == '__main__':
    try:
        json_filename = sys.argv[1].strip() # config.json
        node_id = int(sys.argv[2].strip()) # 0

        addrs, cur_addr = load_conf(json_filename, node_id)
        cluster = Cluster(addrs)

        node = cluster[node_id] # this line is not used

        timer_thread = TimerThread(node_id, cluster)
        timer_thread.start()
        
        app.run(host=cur_addr['ip'], port=cur_addr['port'])
    except KeyboardInterrupt:
        pass
