import collections

Node = collections.namedtuple('Node', ['id', 'uri'])
CLUSTER_SIZE = 5 # TODO: Change later # of nodes
ELECTION_TIMEOUT_MAX = 10
HEARTBEAT_INTERVAL = float(ELECTION_TIMEOUT_MAX/5)

class Cluster:
    ids = range(0, CLUSTER_SIZE)
    uris = [f'localhost:500{i}' for i in ids] # TODO: change later

    def __init__(self):
        self._nodes = [Node(id, uri) for id, uri in enumerate(self.uris, start=0)]
    
    def __len__(self):
        return len(self._nodes)
    
    def __getitem__(self, index):
        return self._nodes[index]
    
    def __repr__(self) -> str:
        return ", ".join([f'{node.id}->{node.uri}' for node in self._nodes])

if __name__ == '__main__':
    cluster = Cluster()
    print(cluster)
    