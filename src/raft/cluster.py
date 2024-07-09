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

## python3 src/raft/cluster.py
if __name__ == '__main__':
    addrs = [
        {"ip": "127.0.0.1", "port": 8567},
        {"ip": "127.0.0.1", "port": 9123},
        {"ip": "127.0.0.1", "port": 8889}
    ]
    cluster = Cluster(addrs)
    print(cluster) # 0 -> http://127.0.0.1:8567, 1 -> http://127.0.0.1:9123, 2 -> http://127.0.0.1:8889
    print(cluster[0]) # get the 0-th node instance: Node(id=0, uri='http://127.0.0.1:8567')

    # Two ways to get 0-th node's id: 0
    print(cluster[0][0])
    print(cluster[0].id)

    # Two ways to get 0-th node's uri: http://127.0.0.1:8567
    print(cluster[0][1])
    print(cluster[0].uri)

    