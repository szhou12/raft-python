import os
import json
import time
import socket
import random
import logging

from .log import Log
from .config import config

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logger.propagate = False

class Node(object):
    def __init__(self, metadata: dict):
        self.role = 'follower'

        self.group_id = metadata['group_id']
        # current raft peer's index in peers ????
        self.id = metadata['id']
        # current raft peer's ip:port
        self.addr = metadata['addr']
        # RPC clients of all raft peers
        self.peers = metadata['peers']

        # TODO
        self.conf = self.load_conf()
        self.path = self.conf.node_path
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # persistent state
        self.current_term = 0
        self.voted_for = None

        if not os.path.exists(self.id):
            os.mkdir(self.id)
        
        # init persistent state
        self.load()
        self.log = Log(self.id) ## ????

        # volatile state
        self.commit_index = 0
        self.last_applied = 0

        # volatile state on leader
        self.next_index = {id: self.log.last_log_index + 1 for id in self.peers}
        self.match_index = {id: -1 for id in self.peers}

        # append entries
        self.leader_id = None

        # request vote
        self.vote_ids = {id: 0 for id in self.peers}

        # client request
        self.client_addr = None

        # timeout
        self.timeout = (10, 20)
        self.next_leader_election_time = time.time() + random.randint(*self.timeout)
        self.next_heartbeat_time = 0

        # rpc
        self.rpc_endpoint = Rpc(self.addr, timeout=2)

        # log
        log_format = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(funcName)s [line:%(lineno)d] %(message)s')
        handler = logging.FileHandler(os.path.join(self.path, f'{self.group_id}_{self.id}.log'))
        handler.setFormatter(log_format)
        logger.addHandler(handler)


    # TODO: update later
    @staticmethod
    def load_conf():
        env = os.environ.get("env")
        conf = config[env] if env else config['DEV']
        return conf
    
    

