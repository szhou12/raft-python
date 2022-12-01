from .NodeState import NodeState
import logging

logging.basicConfig(format='%(asctime)s-%(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

class Follower(NodeState):
    def __init__(self, node, cluster):
        super(Follower, self).__init__(node, cluster)
        self.commit_index = 0
        self.last_applied_index = 0
        # self.entries = []
        # self.next_index = 0 # next log entry to be sent by Leader
        # self.match_index = 0 # index of highest log entry to be replicated on server
        self.vote_for = None # Candidate ID that I voted
        self.leader = None
        
    
    def __repr__(self):
        return f'{type(self).__name__}, id={self.node.id}, term={self.current_term}'