import time
import threading
from random import randrange
import logging
from .cluster import ELECTION_TIMEOUT_MAX, TIMEOUT_SCALER, HEARTBEAT_INTERVAL
from .Candidate import Candidate, VoteRequest
from .Follower import Follower
from .Leader import Leader, AppenEntriesRequest


logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

class TimerThread(threading.Thread):
    def __init__(self, node_id, cluster):
        threading.Thread.__init__(self)
        self.cluster = cluster
        self.node = cluster[node_id]
        self.node_state = Follower(self.node, self.cluster)
        self.election_timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX)) * TIMEOUT_SCALER
        self.election_timer = threading.Timer(self.election_timeout, self.become_candidate)
    
    def run(self):
        '''
        Override Thread.run()
        When a thread/node init, it firstly becomes a Follower
        '''
        self.become_follower()
    
    def become_follower(self):
        # Follower becomes Candidate after timeout collapses
        # randomizes timeout in case of >2 nodes timeout at the same time
        timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX)) * TIMEOUT_SCALER
        if type(self.node_state) != Follower:
            logging.info(f'{self} now becomes Follower...')
            self.node_state = Follower(self.node, self.cluster)
        logging.info(f'{self} reset election timer {timeout}s ...')
        self.election_timer.cancel() # reset every time it receives heartbeat
        self.election_timer = threading.Timer(timeout, self.become_candidate)
        self.election_timer.start()
    
    def become_candidate(self):
        logging.warning(f'Heartbeat is timeout: {int(self.election_timeout)}s')
        logging.info(f'{self} becomes Candidate and starts requesting votes...')
        self.node_state = Candidate(self.node_state)
        self.node_state.elect()
        if self.node_state.win():
            self.become_leader()
        else:
            self.become_follower()
    
    def become_leader(self):
        logging.info(f'{self} beomes Leader and starts sending heartbeat...')
        self.node_state = Leader(self.node_state)
        self.node_state.heartbeat()
    
    # invoked in app2.py
    def vote(self, vote_request: VoteRequest):
        '''
        As Follower (node_state), vote for Candidate
        Invoke NodeState.vote()
        '''
        logging.info(f'{self} received vote request: {vote_request}')
        vote_result = self.node_state.vote(vote_request)
        logging.info(f'{self} returns vote result: {vote_result}')

        if vote_result[0]: # result['vote_granted']
            self.node_state.current_term = vote_result[1]
            self.become_follower()
        return vote_result
    

    # Leader rule 2: Leader responding to client
    def client_append_entries(self, client_request):
        '''
        Add client's PUT request to Leader's local log
        Arg:
            client_request: str
        '''
        result = self.node_state.client_append_entries(client_request)

        # NOTE: postpone response to client until entry applied to state machine
        time.sleep(HEARTBEAT_INTERVAL)
        return result
    
    # Leader rule 2: Leader responding to client
    def fetch_MQ(self):
        '''
        MQ saved in log, fetch the latest commited (commit_index - 1) MQ from Leader's log
        '''
        # NOTE: postpone until entry applied to state machine
        time.sleep(HEARTBEAT_INTERVAL)
        
        result = self.node_state.fetch_MQ()
        return result

    
    def append_entries(self, append_entries_request: AppenEntriesRequest):
        '''
        As Follower (node_state), append entries from Leader log or receive heartbeat
        Invoke NodeState.append_entries()
        '''
        logging.info(f'{self} received append entries request: {append_entries_request}')
        append_result = self.node_state.append_entries(append_entries_request)
        logging.info(f'{self} returns append entries result: {append_result}')
        
        # if append_result[0]: # result['success']
        #     self.node_state.current_term = append_result[1]
        #     self.become_follower() # TODO: outside if ????
        #     # set leader id
        #     self.node_state.leader = append_entries_request['leader_id']
        
        self.node_state.current_term = append_result[1]
        self.become_follower() # Follower remains its role
        # set leader id
        self.node_state.leader = append_entries_request['leader_id']
        
        return append_result


    
    def __repr__(self):
        return f'{type(self).__name__, self.node_state}'








