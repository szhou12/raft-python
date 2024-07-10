# Raft REST Message Queue (RRMQ)

## Dependencies
```
pip install -r requirements.txt
```

## Virtual Environment
Recommend creating a virtual environment to work on this project.

For example:
```
conda create --name <env-name> python=3.9 
```

## Implementation and API Specifications
### Starting the Server
```linux
> python3 src/node.py <path_to_config> index
```
* `<path_to_config>`: the path to a JSON file with a list of the IP and port of all the nodes in the RRMQ (relative to the root folder of the repository).
* `index`: the index of the current server in that JSON list of addresses that will be used to let the server know its own IP and port.

For example, a system with 3 local nodes on ports 8567, 9123, 8889 would have the following `config.json` file:
```json
{
    addresses: 
    [
        {"ip": "127.0.0.1", "port": 8567},
        {"ip": "127.0.0.1", "port": 9123},
        {"ip": "127.0.0.1", "port": 8889}
    ]
}
```
And we would start this system with the following commands in 3 separate terminals:
```linux
> python3 src/node.py config.json 0 # will be on http://127.0.0.1:8567
> python3 src/node.py config.json 1 # will be on http://127.0.0.1:9123
> python3 src/node.py config.json 2 # will be on http://127.0.0.1:8889
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
Using `pytest`