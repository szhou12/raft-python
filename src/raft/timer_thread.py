import sys
import threading
from random import randrange
import logging

from monitor import send_state_update

from Candidate import Candidate
from Follower import Follower
from Leader import Leader
from cluster import Cluster, ELECTION_TIMEOUT_MAX

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

cluster = Cluster()

class TimerThread(threading.Thread):
    def __init(self, node_id):
        threading.Thread.__init__(self)
    
    def run(self):
        '''
        When a thread/node init, it firstly becomes a Follower
        '''
        self.become_follower()
    
    def become_follower(self):
        # Follower becomes Candidate after timeout collapses
        # randomizes timeout in case of >2 nodes timeout at the same time
        timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX))
        if type(self.node_state) != Follower:
            logging.info(f'{self} now becomes Follower ...')
            self.node_state = Follower(self.node)
        logging.info(f'{self} reset election timer {timeout}s ...')
        self.election_timer.cancel() # reset every time it receives heartbeat
        self.election_timer = threading.Timer(timeout, self.become_candidate)
        self.election_timer.start()



