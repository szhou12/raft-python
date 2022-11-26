import collections

import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

VoteResult = collections.namedtuple('VoteResult', ['vote_granted', 'term', 'id'])

class NodeState:
    def __init__(self, node=None):
        self.cluster = Cluster()
        self.node = node
        self.id = node.id
        self.current_term = 0
        self.vote_for = None # node ID of the voted Candidate
    
    def vote(self, vote_request):
        '''
        Args:
            vote request from candidate
        Return:
            vote_granted: bool
            term: current_term for candidate to update
            id: current node's id
        Rules:
            1. False if candidate_term < current_term
            2. True if (vote_for is None or vote_for == candidate_id) and candidate's log is newer
        '''
        candidate_term = vote_request['term']
        candidate_id = vote_request['candidate_id']
        if candidate_term > self.current_term:
            logging.info(f'{self} accepts vote request as term: {candidate_term} > {self.current_term}')
            self.vote_for = candidate_id
            self.current_term = candidate_term
            return VoteResult(True, self.current_term, self.id)
        if candidate_term < self.current_term:
            logging.info(f'{self} rejects vote request as term: {candidate_term} < {self.current_term}')
            return VoteResult(False, self.current_term, self.id)
        if self.vote_for is None or self.vote_for == candidate_id:
            # TODO: check if the candidate's log is newer than receiver's
            self.vote_for = candidate_id
            return VoteResult(True, self.current_term, self.id)
        logging.info(f'{self} rejects vote request as vote_for id: {self.vote_for} != {candidate_id}')
        return VoteResult(False, self.current_term, self.id)
    
    def win(self):
        '''
        Another running thread may change the node state to Follower when received heartbeat
        Only Candidate can return True
        Both Leader and Follower return False
        '''
        return False