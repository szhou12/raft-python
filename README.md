# Raft REST Message Queue (RRMQ)

## Table of Contents
* [Dependencies](#dependencies)
* [Virtual Environment](#virtual-environment)
* [Implementation and API Specifications](#implementation-and-api-specifications)
  * [Starting the Server](#starting-the-server)
  * [REST API](#rest-api)
    * [Topic](#topic)
    * [Message](#message)
    * [Status](#status)
* [Testing](#testing)
    * [Manual Testing](#manual-testing)
    * [Using `pytest`](#using-pytest)

## Dependencies
```
pip install -r requirements.txt
```

## Virtual Environment
Highly recommend creating a virtual environment to work on this project.

For example:
```
conda create --name network python=3.9 
```

**NOTE**: If you are using a conda environment, it's better to check which Python interpreter the conda environment is referring to.
1. Check the Python Interpreter:
```linux
which python
```
It's likely to output: `/opt/anaconda3/envs/network/bin/python`

This means the current conda env is referring to `python`. Thus, whenever you need to run Python scripts in the terminal, you should use `> python` instead of `> python3`.

## Implementation and API Specifications
### Starting the Server
```linux
> python src/node.py <path_to_config> index
```
* `<path_to_config>`: the path to a JSON file with a list of the IP and port of all the nodes in the RRMQ (relative to the root folder of the repository).
* `index`: the index of the current server in that JSON list of addresses that will be used to let the server know its own IP and port.

For example, a system with 3 local nodes on ports 8567, 9123, 8889 would have the following `config.json` file:
```json
{
    "addresses": 
    [
        {"ip": "127.0.0.1", "port": 8567},
        {"ip": "127.0.0.1", "port": 9123},
        {"ip": "127.0.0.1", "port": 8889}
    ]
}
```
And we would start this system with the following commands in 3 separate terminals:
```linux
> python src/node.py config.json 0 # will be on http://127.0.0.1:8567
> python src/node.py config.json 1 # will be on http://127.0.0.1:9123
> python src/node.py config.json 2 # will be on http://127.0.0.1:8889
```

### REST API
The REST API has three endpoints: **Topic**, **Message**, and **Status**. Note: in addition to the response types described here, the REST API should return appropriate HTTP codes in response to different events.

#### Topic
The topic endpoint is used to create a topic and retrieve a list of topics. Topics are simply **string** names.

##### PUT /topic
Used to create a new topic.
* Flask endpoint: `@app.route('/topic', methods=['PUT'])`
* Body: `{'topic' : str}` 
* Returns: `{'success' : bool}`

Returns True if the topic was created, False if the topic could not be created (e.g., if the topic name already exists).

##### GET /topic
Used to get a list of topics.
* Flask endpoint: `@app.route('/topic', methods=['GET'])`
* Returns: `{'success' : bool, 'topics' : [str]}`

If there are no topics it returns an empty list.

#### Message
The message endpoint is used to add a message to a topic and get a message from a topic.

##### PUT /message
Used to add a message to a topic.
* Flask endpoint: `@app.route('/message', methods=['PUT'])`
* Body: `{'topic' : str, 'message' : str}` 
* Returns: `{'success' : bool}`

Returns True if the message was added and False if the message could not be added (e.g., if the topic does not exist).

##### GET /message
Used to pop a message from the topic. Notice that the topic name is encoded in the URL.
* Flask endpoint: `@app.route('/message/<topic>', methods=['GET'])`
* Returns: `{'success' : bool, 'message' : str}`

Returns False if the topic does not exist or there are no messages in the topic that haven’t been already consumed.

#### Status
The status endpoint is used for testing the leader election algorithm.

##### GET /status
* Flask endpoint: `@app.route('/status', methods=['GET'])`
* Returns: `{'role' : str, 'term' : int}`

Role may be one of three options: Leader, Candidate, Follower. 

Term is the node’s current term as an integer.

## Testing
### Manual Testing
Need to invoke main functions in `src/node.py` and `src/client.py` respectively.

Imagine `client.py` as user who sends requests and receives responses; `node.py` as server node who recieves requests, stores info, and returns responses.

Suppose we want to inspect 3 server nodes running on ports 8567, 9123, 8889. We need to do the following 2 steps in order:
1. Open 3 terminals and start 3 server nodes in each thread:
```linux
// start a thread for node 0 on port 8567:
> python src/node.py config.json 0
```
2. Open 4th terminal and run client:
```linux
// client sends requests and receives responses from server node 0 on port 8567:
> python src/client.py 8567
```


### Using `pytest`
1. Test on one specific test case `test_get_topic_empty()`:
```linux
pytest test/message_queue_test.py::test_get_topic_empty
```
2. Test all test cases in `test/message_queue_test.py`:
```linux
pytest test/message_queue_test.py
```
3. Test all test cases in `test/election_test.py`:
```linux
pytest test/election_test.py
```
4. Test all test cases in `test/replication_test.py`:
```linux
pytest test/replication_test.py
```

### Repeat Testing
If you want to repeatedly execute the `pytest` for a specified number of times (in order to test the performance on specific parameters values: number of nodes, timeout, etc.), you can execute the following Bash command:
```linux
./run_tests.sh 10 test/election_test.py
```
This script will run pytest test/election_test.py 10 times.