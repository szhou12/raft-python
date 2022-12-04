import collections

import os
import json
from .cluster import Cluster
from .Log import Log
import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

VoteResult = collections.namedtuple('VoteResult', ['vote_granted', 'term', 'id'])
AppendEntriesResult = collections.namedtuple('AppendEntriesResult', ['success', 'term', 'id'])

STORAGE_PATH = './data'

class NodeState:
    def __init__(self, node=None, cluster=None):
        self.cluster = cluster
        self.node = node # Node(id, uri)
        self.id = node.id
        
        ## Volatile state
        self.commit_index = 0
        self.last_applied_index = 0

        ## Persistent state
        if not os.path.exists(STORAGE_PATH):
            os.makedirs(STORAGE_PATH)

        self.current_term = 0
        self.vote_for = None # Candidate ID that me as Follower voted
        self.load()
        log_filename = os.path.join(STORAGE_PATH, f'{self.id}_log.json')
        self.log = Log(log_filename) # log_entries[]
    
    def load(self):
        '''
        Read persistent states from storage:
            - current_term 
            - vote_for
        '''
        filename = os.path.join(STORAGE_PATH, f'{self.id}_states.json')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            self.current_term = data['current_term']
            self.vote_for = data['vote_for']
        else:
            self.save()
    
    def save(self):
        '''
        Save persistent states from storage:
            - current_term 
            - vote_for
        '''
        data = {
            'current_term': self.current_term,
            'vote_for': self.vote_for
        }
        filename = os.path.join(STORAGE_PATH, f'{self.id}_states.json')
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    
    def vote(self, vote_request):
        '''
        Me as Follower node reacting to Candidate node's vote request
        Args:
            vote request from candidate:
                - term
                - candidateId
                - lastLogIndex
                - lastLogTerm
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
        candidate_last_log_index = vote_request['last_log_index']
        candidate_last_log_term = vote_request['last_log_term']

        if candidate_term > self.current_term:
            logging.info(f'{self} accepts vote request as Candidate term: {candidate_term} > {self.current_term}')
            self.vote_for = candidate_id
            self.current_term = candidate_term
            self.save()
            return VoteResult(True, self.current_term, self.id)

        if candidate_term < self.current_term:
            logging.info(f'{self} rejects vote request as Candidate term: {candidate_term} < {self.current_term}')
            return VoteResult(False, self.current_term, self.id)

        # RequestVote RPC Rule 2
        if self.vote_for is None or self.vote_for == candidate_id:
            # Check if the candidate's log is newer than receiver's
            if candidate_last_log_index >= self.log.last_log_index and candidate_last_log_term >= self.log.last_log_term:
                logging.info(f'{self} accepts vote request as Candidate log is newer')
                self.vote_for = candidate_id
                self.save()
                return VoteResult(True, self.current_term, self.id)
            else:
                logging.info(f'{self} rejects vote request as Candidate log too old')
                self.vote_for = None
                self.save()
                return VoteResult(False, self.current_term, self.id)

        logging.info(f'{self} rejects vote request as vote_for id: {self.vote_for} != {candidate_id}')
        return VoteResult(False, self.current_term, self.id)
    
    def win(self):
        '''
        Another running thread may change the node state to Follower when received heartbeat
        Only Candidate can return True
        Both Leader and Follower return False
        '''
        return False
    
    def client_append_entries(self, client_request):
        '''
        Me as Leader node reacting to client's request
        Leader Rule #2:
            If command received from client: append entry to local log, 
            respond after entry applied to state machine
        Arg:
            client_request: str
        '''
        new_entry = {"message": client_request, "term": self.current_term}
        self.log.append_entries(self.log.last_log_index, [new_entry])
        logging.info(f'{self} append new entry to local log from client request: {client_request}')
        return {'success': True}
    
    def fetch_MQ(self):
        '''
        Me as Leader node reacting to client's request, fetching latest commited MQ
        MQ info saved in self.log
        '''
        return self.log.get_log_message(self.commit_index - 1)
    
    def append_entries(self, append_entries_request):
        leader_term = append_entries_request['term']
        leader_prev_log_index = append_entries_request['prev_log_index']
        leader_prev_log_term = append_entries_request['prev_log_term']
        leader_entries = append_entries_request['entries']
        leader_commit_index = append_entries_request['leader_commit']

        # All Servers Rule 2
        if leader_term > self.current_term:
            self.current_term = leader_term
            self.save()

        if leader_term < self.current_term:
            logging.info(f'{self} rejects append entries request as Leader term: {leader_term} < {self.current_term}')
            return AppendEntriesResult(success=False, term=self.current_term, id=self.id)
        
        result = AppendEntriesResult(success=False, term=self.current_term, id=self.id)
        if not leader_entries:
            logging.info('heartbeat')
            result = result._replace(success=True)
        else:
            if leader_prev_log_term != self.log.get_log_term(leader_prev_log_index):
                logging.info(f'{self} rejects append entries request as index not match or term not match')
                self.log.delete_entries(leader_prev_log_index)
            else:
                logging.info(f'{self} accepts append entries request')
                self.log.append_entries(leader_prev_log_index, leader_entries)
                result = result._replace(success=True)
        
        # Append Entries Rule 5: reset Follower's commit index
        if leader_commit_index > self.commit_index:
            self.commit_index = min(leader_commit_index, self.log.last_log_index)
            logging.info(f'{self} commits, commit index: {self.commit_index}')
        
        return result
        



