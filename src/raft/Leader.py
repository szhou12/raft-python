import time
from random import randrange
import json
import grequests
from .NodeState import NodeState
from .client import Client
from .cluster import HEARTBEAT_INTERVAL, ELECTION_TIMEOUT_MAX
import logging

# from .monitor import send_state_update, send_heartbeat

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

class AppenEntriesRequest:
    def __init__(self, leader, dst_node): # dst_node = Node(id, uri)
        self.term = leader.current_term
        self.leader_id = leader.id
        self.prev_log_index = leader.next_index[dst_node] - 1
        self.prev_log_term = leader.log.get_log_term(leader.next_index[dst_node]-1)
        self.entries = leader.log.get_entries(leader.next_index[dst_node])
        self.leader_commit = leader.commit_index
    
    def to_json(self):
        return json.dumps(
            self,
            default=lambda obj: obj.__dict__,
            sort_keys=True,
            indent=4
        )



class Leader(NodeState):
    def __init__(self, candidate):
        super(Leader, self).__init__(candidate.node, candidate.cluster)
        self.current_term = candidate.current_term # read from persistent data????
        # self.commit_index = candidate.commit_index
        # self.last_applied_index = candidate.last_applied_index
        # self.entries = candidate.entries
        self.stopped = False
        self.followers = [peer for peer in self.cluster if peer != self.node]
        self.election_timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX)) # no use DELETE???
        self.next_index = {peer: self.log.last_log_index + 1 for peer in self.followers}
        self.match_index = {peer: 0 for peer in self.followers}


    def heartbeat(self):
        while not self.stopped:
            logging.info(f'{self} sending heartbeat to followers...')
            logging.info('====================================================>')
            # send_heartbeat(self, HEARTBEAT_INTERVAL) # TODO: implement this
            client = Client()
            with client as session:
                posts = [
                    grequests.post(f'{peer.uri}/raft/heartbeat', json=self.node, session=session)
                    for peer in self.followers
                ]
                for response in grequests.map(posts, gtimeout=HEARTBEAT_INTERVAL): # stop waiting for response after heartbeat time
                    if response is not None:
                        logging.info(f'{self} received heartbeat response from follower: {response.json()}')
                    else:
                        logging.info(f'{self} received heartbeat response from follower: None')

            logging.info('==================================================END')
            time.sleep(HEARTBEAT_INTERVAL)
    
    def __repr__(self):
        return f'{type(self).__name__}, id={self.node.id}, term={self.current_term}'
