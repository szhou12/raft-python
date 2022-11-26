import sys
import os
from flask import Flask, request, jsonify
import logging
import json
from raft.cluster import Cluster
from raft.timer_thread import TimerThread

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

NODE_ID = int(os.environ.get('NODE_ID'))
cluster = Cluster()
node = cluster[NODE_ID]
timer_thread = TimerThread(NODE_ID)

def create_app():
    raft = Flask(__name__)
    timer_thread.start()
    return raft

app = create_app()

@app.route('/raft/vote', methods=['POST'])
def request_vote():
    '''
    When a Follower timeout, it becomes a Candidate and starts election by POSTing vote requests to other nodes
    '''
    candidate_vote_request = request.get_json()
    result = timer_thread.vote(json.loads(candidate_vote_request)) # Follower thread to vote
    return jsonify(result) # return voting result to Candidate

@app.route('/raft/heartbeat', methods=['POST'])
def heartbeat():
    '''
    When a node becomes Leader, it will POST heartbeat requests to other nodes
    '''
    leader = request.get_json()
    logging.info(f'{timer_thread} got heartbeat from Leader: {leader}')
    response = {"alive": True, "node": node}
    timer_thread.become_follower() # once receives heartbeat, the node maintains as Follower
    return jsonify(response)


# TODO: MODIFY LATER
# return info of this raft cluster
@app.route('/')
def hello_raft():
    return f'raft cluster: {cluster}!'

if __name__ == 'main':
    try:
        create_app()
        app.run()
    except KeyboardInterrupt:
        pass
