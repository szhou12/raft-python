import time
from random import randrange
import json
import grequests
from .NodeState import NodeState
from .client import Client
from .cluster import HEARTBEAT_INTERVAL, ELECTION_TIMEOUT_MAX
import logging


logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

class AppenEntriesRequest:
    def __init__(self, leader, follower_id):
        self.term = leader.current_term
        self.leader_id = leader.id
        self.prev_log_index = leader.next_index[follower_id] - 1
        self.prev_log_term = leader.log.get_log_term(leader.next_index[follower_id]-1)
        self.entries = leader.log.get_entries(leader.next_index[follower_id])
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
        self.current_term = candidate.current_term
        self.vote_for = None # once node becomes Leader, reset vote_for=None
        self.save()
        self.stopped = False
        self.followers = [peer for peer in self.cluster if peer != self.node]
        self.next_index = {peer.id: self.log.last_log_index + 1 for peer in self.followers}
        self.match_index = {peer.id: 0 for peer in self.followers}


    def heartbeat(self):
        while not self.stopped:
            logging.info(f'{self} sending heartbeat to followers...')
            logging.info('====================================================>')
            client = Client()
            with client as session:
                posts = [
                    grequests.post(f'{peer.uri}/raft/heartbeat', json=AppenEntriesRequest(self, peer.id).to_json(), session=session)
                    for peer in self.followers
                ]
                for response in grequests.map(posts, gtimeout=HEARTBEAT_INTERVAL):
                    if response is not None:
                        result = response.json()
                        logging.info(f'{self} received heartbeat response from follower: {result}')
                        if result[0]: # result['success'] == True
                            self.match_index[result[2]] = self.next_index.get(result[2])
                            self.next_index[result[2]] = self.log.last_log_index + 1
                        else:
                            self.next_index[result[2]] -= 1
                            self.next_index[result[2]] = max(0, self.next_index[result[2]])

                    else:
                        logging.info(f'{self} received heartbeat response from follower: None')

            logging.info('=====================================================')
            
            
            ## Update Leader's commit index
            ## if update, commit index points to the next position of the latest commited log
            if not self.followers: # Edge case: If only Leader node exists, directly incremenet commit_index
                self.commit_index = self.log.last_log_index + 1
                logging.info(f'{self} alone commits, commit index: {self.commit_index}')

            N = self.commit_index + 1
            count = 0
            for id in self.match_index:
                if self.match_index[id] >= N:
                    count += 1
                if count >= len(self.followers) // 2:
                    self.commit_index = N
                    logging.info(f'{self} commits, commit index: {self.commit_index}')
                    break
            time.sleep(HEARTBEAT_INTERVAL)
    
    def __repr__(self):
        return f'{type(self).__name__}, id={self.node.id}, term={self.current_term}'
