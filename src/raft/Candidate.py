from .NodeState import NodeState
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
        # self.last_log_index = candidate.log.last_log_index
        # self.last_log_term = candidate.log.last_log_term
    
    def to_json(self):
        return json.dumps(
            self,
            default=lambda obj: obj.__dict__,
            sort_keys=True,
            indent=4
        )

class Candidate(NodeState):
    def __init__(self, follower):
        super(Candidate, self).__init__(follower.node, follower.cluster)
        self.current_term = follower.current_term
        self.vote_for = self.id # Candidate always votes itself
        self.save()
        # self.commit_index = follower.commit_index
        # self.last_applied_index = follower.last_applied_index
        self.votes = []
        # self.entries = follower.entries
        self.followers = [peer for peer in self.cluster if peer != self.node]
        
    
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
        self.save()
        logging.info(f'{self} sending vote requests to peers...')
        client = Client() # init an http client
        with client as session:
            posts = [
                grequests.post(f'{peer.uri}/raft/vote', json=VoteRequest(self).to_json(), session=session)
                for peer in self.followers
            ]
            for response in grequests.imap(posts):
                result = response.json()
                logging.info(f'{self} received vote result: {response.status_code}: {result}')
                if result[0]: # result['vote_granted'] == True
                    self.votes.append(result[2]) # append vote_granted node id


    def win(self):
        logging.warning(f'win: votes {len(self.votes)}; total: {len(self.cluster)}')
        return len(self.votes) > len(self.cluster) / 2
    
    def __repr__(self):
        # return f'{type(self).__name__, self.node.id, self.current_term}'
        return f'{type(self).__name__}, id={self.node.id}, term={self.current_term}'

                

