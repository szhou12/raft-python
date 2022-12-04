# Technical Report

## Message Queue
### Design & Implementation
The implementation of message queue follows the instruction from project handout section 5.2. Dictionary is the data structure used for storing the message queue and the topics. MQ interface is further extended in a way such that it can maintain consistency between state by applying the Raft consensus algorithm.

Some key extended parts include but not limited to:
- The state of message queue is stored in each node's log. In other words, each log entry not only serves to contain command for state machine, but also serves as the "database" where client's requested data are fetched from.
- Every time a client makes a RPC, the corresponding RPC endpoint will load the latest commited state of MQ from leader's log, make changes to the MQ by executing GET/PUT operation, and finally append new state of MQ to leader's log, which will be replicated to followers' logs before responding to the client.

### Possible Shortcomings




## Leader Election
### Design & Implementation

The design of Leader Election algorithm follows RAFT paper: every node is initialized to be a Follower. When any of Follower node's election timeout elapses, this node will become a candidate and start the election. In order to avoid the conflicted situation where two nodes become candidates at the same time and as a result receive same number of votes. Each node's election timeout is randomized. If a Candidate node receives majority votes, it will become a Leader node. Otherwise, it will be converted back to Follower.

As for implemenation, my choice was to create a parent class `NodeState` that contains core fields that are required for all roles (Follower, Candidate, Leader) and core behaviors such as dealing with RequestVote RPC and AppendEntries RPC. `Follower` and `Candidate` are two classes that inherit from `NodeState` and contain more fields that needed to be addressed on their levels. `Candidate` is additionally responsible for starting the election: encapsulates vote requests, asynchronously send them to all followers over RPC, and collects vote results.

### Possible Shortcomings
The current implementation is able to pass election timeout set to 300ms.




## Log Replication
### Design & Implementation

### Possible Shortcomings


## Resources
