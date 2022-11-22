import sys
from flask import request
from flask import Flask
from flask import jsonify

HOST = '127.0.0.1'

app = Flask(__name__)

topics = {}

@app.route('/topic', methods=['GET'])
def get_all_topics():
    topic_list = list(topics.keys())
    print(topic_list)
    if len(topic_list) > 0:
        statement = {'success': True, 'topics': topic_list}
        return jsonify(statement)
    else:
        statement = {'success': False, 'topics': topic_list}
        return jsonify(statement)


@app.route('/topic', methods=['PUT'])
def add_new_topic():
    new_topic = request.json['topic']

    if new_topic in topics:
        return jsonify({'success': False})
    
    topics[new_topic] = []
    return jsonify({'success': True})


@app.route('/message', methods=['PUT'])
def add_message():
    topic = request.json['topic']

    if topic not in topics:
        return jsonify({'success': False})
    
    message = request.json['message']
    topics[topic].append(message)
    return jsonify({'success': True})

@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if topic not in topics or len(topics[topic]) == 0:
        return jsonify({'success': False, 'message': ''})
    
    message = topics[topic][0]
    topics[topic] = topics[topic][1:]
    return jsonify({'success': True, 'message': message})


#TODO
@app.route('/status', methods=['GET'])
def get_status():
    '''
    return: {'role': <str>, 'term': <int>}
    role options: Leader, Candidate, Follower
    term: the node's current term as an integer
    '''
    pass


IP = '127.0.0.1'

if __name__ == '__main__':
    try:
        port = int(sys.argv[1].strip())
        app.run(host=IP, port=port, debug=True)

    except KeyboardInterrupt:
        pass