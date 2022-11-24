import os
import json
import time
import socket
import random
import logging
from timer import ResettableTimer
import dataclasses
from dataclasses import dataclass
from enum import Enum

from .log import Log
from .config import config

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logger.propagate = False

class Role(Enum):
    Follower = "Follower"
    Leader = "Leader"
    Candidate = "Candidate"

@dataclass
class PersistentState:
    pass


@dataclass
class LogEntry:
    message: str
    term: int


@dataclass
class VoteRequest:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int

    
class Node(object):
    def __init__(self, metadata: dict):
        self.role = Role.Follower

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
    
    def load(self):
        filename = os.path.join(self.path, f'{self.group_id}_{self.id}_persist.json')
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                persist_data = json.load(f)
            self.current_term = persist_data['current_term']
            self.voted_for = persist_data['voted_for']
        else:
            self.save()

    def save(self):
        filename = os.path.join(self.path, f'{self.group_id}_{self.id}_persist.json')
        persist_data = {
            'current_term': self.current_term,
            'voted_for': self.voted_for
        }
        with open(filename, 'w') as f:
            json.dump(persist_data, f, indent=4)

    def redirect(self, data, addr):
        '''
        Redirect to Leader node
        Args:
            data: dict
            addr: tuple(ip, port)
        Return:
            dict // Change it to response {'success': bool, 'data': dict}
        '''
        if not data:
            return {} # TODO
        
        if data.get('type') == 'client_append_entries':
            if self.role != Role.Leader:
                if self.leader_id:
                    logger.info(f"redirect client_append_entries to leader node: {self.leader_id}")
                    self.rpc_endpoint.send(data, self.peers.get(self.leader_id)) # TODO: change later
                return {} # TODO
            else: # me is leader node
                self.client_addr = (addr[0], self.conf.cport)
                return data # TODO
        
        if data.get('dst_id') != self.id:
            logger.info(f"redirect to: {data.get('dst_id')}")
            self.rpc_endpoint.send(data, self.peers.get(data.get('dst_id')))
            return {} # TODO
        
        return data
    
    def append_entries():
        '''
        Append Entries RPC
        Invoked by leader to replicate log entries; also used as heartbeat
        '''
        # TODO
        pass

    def request_vote():
        '''
        RequestVote RPC
        Invoked by candidates to gather votes
        '''

    


