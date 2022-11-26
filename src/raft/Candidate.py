from NodeState import NodeState
import grequests
import json
from .client import Client
import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

class VoteRequest:
    def __init__(self, candidate):
        self.candidate_id = candidate.id
        self.term = candidate.current_term
        # TODO: init log info when implement raft log replication
        self.last_log_index = 0
        self.last_log_term = 0
    
    def to_json(self):
        return json.dumps(
            self,
            default=lambda obj: obj.__dict__,
            sort_keys=True,
            indent=4
        )

class Candidate(NodeState):
    def __init__(self, follower):
        super(Candidate, self).__init__(follower)
        self.current_term = follower.current_term
        self.commit_index = follower.commit_index
        self.last_applied_index = follower.last_applied_index
        self.votes = []
        self.entries = follower.entries
        self.followers = [peer for peer in self.cluster if peer != self.node]
        self.vote_for = self.id # Candidate always votes itself
    
    def elect(self):
        '''
        When this node becomes Candidate, it shall start election:
            step 1: current_term + 1
            step 2: vote itself
            step 3: send vote request to each peer node concurrently
            step 4: return when timeout
        '''
        self.current_term += 1
        self.votes.append(self.node) # vote itself
        logging.info(f'{self} sending vote requests to peers...')
        client = Client() # init an http client
        with client as session:
            posts = [
                grequests.post(f'http://{peer.uri}/raft/vote', json=VoteRequest(self).to_json(), session=session)
                for peer in self.followers
            ]
            for response in grequests.imap(posts):
                result = response.json()
                logging.info(f'{self} received vote result: {response.status_code}: {result}')
                ## NOTE: need to check if works
                # if result[0]:
                #     self.votes.append(result[2])
                if result['vote_granted']:
                    self.votes.append(result['id'])
    
    def win(self):
        return len(self.votes) > len(self.cluster) / 2
    
    def __repr__(self):
        return f'{type(self).__name__, self.node.id, self.current_term}'

                

