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
    leader = request.get_json()
    logging.info(f'{timer_thread} got heartbeat from Leader: {leader}')
    response = {"alive": True, "node": node}
    timer_thread.become_follower() # once receives heartbeat, this node maintains as Follower
    return jsonify(response)


# TODO: MODIFY LATER
# return info of this raft cluster
@app.route('/')
def hello_raft():
    return f'raft cluster: {cluster}!'



def load_conf(filename, node_id, key="addresses"):
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return (config[key], config[key][node_id])
    except FileNotFoundError:
        logging.warning('Config file NOT Found!')



### python3 src/node.py config.json 0
## app2.py -> node.py
if __name__ == 'main':
    try:
        json_filename = sys.argv[1].strip()
        node_id = int(sys.argv[2].strip())
        addrs, cur_addr = load_conf(json_filename)

        # NODE_ID = int(os.environ.get('NODE_ID'))
        cluster = Cluster(addrs)
        node = cluster[node_id]
        timer_thread = TimerThread(node_id, cluster)
        # app = create_app()
        timer_thread.start()
        app.run(host=cur_addr['ip'], port=cur_addr['port'], debug=True)
    except KeyboardInterrupt:
        pass
