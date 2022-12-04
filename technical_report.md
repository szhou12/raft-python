# Technical Report

## Message Queue
### Design & Implementation
The implementation of message queue follows the instruction from project handout section 5.2. Dictionary is the data structure used for storing the message queue and the topics. MQ interface is further extended in a way such that it can maintain consistency between state by applying the Raft consensus algorithm.

Some key extended parts include but not limited to:
- The state of message queue is stored in each node's log. In other words, each log entry not only serves to contain command for state machine, but also serves as the "database" where client's requested data are fetched from.
- Every time a client makes a RPC, the corresponding RPC endpoint will load the latest commited state of MQ from leader's log, make changes to the MQ by executing GET/PUT operation, and finally append new state of MQ to leader's log, which will be replicated to followers' logs before responding to the client.

### Possible Shortcomings

No shortcomings were spotted when testing on single-node message queue.


## Leader Election
### Design & Implementation

The design of Leader Election algorithm follows RAFT paper: every node is initialized to be a Follower. When any of Follower node's election timeout elapses, this node will become a candidate and start the election. In order to avoid the conflicted situation where two nodes become candidates at the same time and as a result receive same number of votes. Each node's election timeout is randomized. If a Candidate node receives majority votes, it will become a Leader node. Otherwise, it will be converted back to Follower.

As for implemenation, my choice was to create a parent class `NodeState` that contains core fields that are required for all roles (Follower, Candidate, Leader) and core behaviors such as dealing with RequestVote RPC and AppendEntries RPC. `Follower` and `Candidate` are two classes that inherit from `NodeState` and contain more fields that needed to be addressed on their levels. `Candidate` is additionally responsible for starting the election: encapsulates vote requests, asynchronously sends them to all followers over RPC, and collects vote results.

Based on the performance on tests, the current implementation is able to pass election timeout set to 300ms.

### Possible Shortcomings

Admittedly, some other descion choices can be to have one `Node` class, use a enum class to dynamically denote a node's state (Follower, Candidate, Leader), and have all fields and behaviors implemented within `Node` class. This design choice, compared to my design, has two advantages: 1. it simplifies the code structure; 2. it decreases the number of I/O for persistent states. (In my design, every time a node switches its role, it will re-initialize `NodeState`, which will reload persistent data)

However, I think my design of having separate classes for defining a node's state makes it efficient for debugging as each class is only responsible for its own behaviors. Thus, one can quickly locate the error when it happens. 


## Log Replication
### Design & Implementation

The design of Log Replication follows RAFT paper: Once there is a Leader node, it will be responisible for sending hearbeats to followers and responding to a client's apeend entries request by encapsulating apeend entries requests, asynchronously sending them to all followers over RPC for replication, and collecting results.

As for implemenation, my choice was to create a `Leader` class that inherits from `NodeState` class. As long as the node remains leader, it will periodically send heartbeats to followers over RPC. If a client's request comes in, the heartbeat will turn into AppendEntries request sent to followers over RPC instead. Whenever a follower receives new logs from leader, it will replicate new logs by appending new logs to its persistent log.

### Possible Shortcomings

Log replication requires follower nodes to check consistency between new logs and log they are maintaining and persist new logs to the storage. This is costly as I/O can take some time. Also, my implemenation utilizes logs as 'database'. As a result, if a client is requesting new information before new logs are saved in followers' storage, there may be chances that the client will not get back new information if the leader is down and a follower becomes a new leader but has not finished writing new logs to its storage.

The experiments on log replication tests on 300ms level show that, on average, there was 10%~20% chance that when a follower becomes the new leader, it fails to return back new information because not enough time is given to it to finish persisting new information to its local log. 


## Resources
[In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf)
[Students' Guide to Raft](https://thesquareplanet.com/blog/students-guide-to-raft/)
[The Raft Consensus Algorithm](https://raft.github.io/)
[Raft实现(2)：选举](https://www.jianshu.com/p/ccf9b8d3633d)
[Raft实现(3)：客户端指令和日志复制](https://www.jianshu.com/p/b9a760c7d64b)
