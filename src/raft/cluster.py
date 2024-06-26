import collections

Node = collections.namedtuple('Node', ['id', 'uri'])

# NOTE: HEARTBEAT_INTERVAL << min(ELECTION_TIMEOUT)
TIMEOUT_SCALER = .001
ELECTION_TIMEOUT_MAX = 300
HEARTBEAT_INTERVAL = float(ELECTION_TIMEOUT_MAX/4) * TIMEOUT_SCALER

class Cluster:

    def __init__(self, addrs):
        self._nodes = [Node(id, f"http://{uri['ip']}:{uri['port']}") for id, uri in enumerate(addrs, start=0)]
    
    def __len__(self):
        return len(self._nodes)
    
    def __getitem__(self, index):
        return self._nodes[index]
    
    def __repr__(self) -> str:
        return ", ".join([f'{node.id} -> {node.uri}' for node in self._nodes])

if __name__ == '__main__':
    addrs = [
        {"ip": "http://127.0.0.1", "port": 8567},
        {"ip": "http://127.0.0.1", "port": 9123},
        {"ip": "http://127.0.0.1", "port": 8889}
    ]
    cluster = Cluster(addrs)
    print(cluster)
    