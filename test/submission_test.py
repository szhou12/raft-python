from test_utils import Swarm, Node, LEADER, FOLLOWER, CANDIDATE

import pytest
import time
import requests

import os
import glob

TEST_TOPIC = "test_topic"
TEST_MESSAGE = "Test Message"
PROGRAM_FILE_PATH = "src/node.py"

# seconds the program will wait after starting a node for election to happen
# it is set conservatively (originally 2s), you will likely be able to lower it for faster testing
ELECTION_TIMEOUT = 0.3 # 300ms

# array of numbr of nodes spawned on tests, an example could be [3,5,7,11,...]
# default is only 5 for faster tests
NUM_NODES_ARRAY = [5]

NUMBER_OF_LOOP_FOR_SEARCHING_LEADER = 3

def clean_persistent_data():
    '''
    Before starting a test, remove persistent data from the previous test first
    '''
    files = glob.glob('./data/*.json', recursive=True)
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))

@pytest.fixture
def node_with_test_topic():
    clean_persistent_data()

    node = Swarm(PROGRAM_FILE_PATH, 1)[0]
    node.start()
    time.sleep(ELECTION_TIMEOUT)
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})
    yield node
    node.clean()


@pytest.fixture
def node():
    clean_persistent_data()

    node = Swarm(PROGRAM_FILE_PATH, 1)[0]
    node.start()
    time.sleep(ELECTION_TIMEOUT)
    yield node
    node.clean()


@pytest.fixture
def swarm(num_nodes):
    clean_persistent_data()

    swarm = Swarm(PROGRAM_FILE_PATH, num_nodes)
    swarm.start(ELECTION_TIMEOUT)
    yield swarm
    swarm.clean()


def collect_leaders_in_buckets(leader_each_terms: dict, new_statuses: list):
    for i, status in new_statuses.items():
        assert ("term" in status.keys())
        term = status["term"]
        assert ("role" in status.keys())
        role = status["role"]
        if role == LEADER:
            leader_each_terms[term] = leader_each_terms.get(term, set())
            leader_each_terms[term].add(i)


def assert_leader_uniqueness_each_term(leader_each_terms):
    for leader_set in leader_each_terms.values():
        assert (len(leader_set) <= 1)


def wait_for_commit(seconds=1):
    time.sleep(seconds)




########################## ELECTION TEST ##########################

@pytest.mark.parametrize('num_nodes', [1])
def test_correct_status_message(swarm: Swarm, num_nodes: int):
    status = swarm[0].get_status().json()
    assert ("role" in status.keys())
    assert ("term" in status.keys())
    assert (type(status["role"]) == str)
    assert (type(status["term"]) == int)


@pytest.mark.parametrize('num_nodes', [1])
def test_leader_in_single_node_swarm(swarm: Swarm, num_nodes: int):
    status = swarm[0].get_status().json()
    assert (status["role"] == LEADER)


@pytest.mark.parametrize('num_nodes', [1])
def test_leader_in_single_node_swarm_restart(swarm: Swarm, num_nodes: int):
    status = swarm[0].get_status().json()
    assert (status["role"] == LEADER)
    swarm[0].restart()
    time.sleep(ELECTION_TIMEOUT)
    status = swarm[0].get_status().json()
    assert (status["role"] == LEADER)


@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_is_leader_elected(swarm: Swarm, num_nodes: int):
    leader = swarm.get_leader_loop(3)
    assert (leader != None)


@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_is_leader_elected_unique(swarm: Swarm, num_nodes: int):
    leader_each_terms = {}
    statuses = swarm.get_status()
    collect_leaders_in_buckets(leader_each_terms, statuses)

    assert_leader_uniqueness_each_term(leader_each_terms)


@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_is_newleader_elected(swarm: Swarm, num_nodes: int):
    leader1 = swarm.get_leader_loop(3)
    assert (leader1 != None)
    leader1.clean(ELECTION_TIMEOUT)
    leader2 = swarm.get_leader_loop(3)
    assert (leader2 != None)
    assert (leader2 != leader1)



########################## LOG REPLICATION TEST ##########################
@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_is_topic_shared(swarm: Swarm, num_nodes: int):
    leader1 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader1 != None)
    assert (leader1.create_topic(TEST_TOPIC).json() == {"success": True})

    leader1.commit_clean(ELECTION_TIMEOUT)
    leader2 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader2 != None)
    assert(leader2.get_topics().json() ==
           {"success": True, "topics": [TEST_TOPIC]})


@pytest.mark.parametrize('num_nodes', NUM_NODES_ARRAY)
def test_is_message_shared(swarm: Swarm, num_nodes: int):
    leader1 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader1 != None)
    assert (leader1.create_topic(TEST_TOPIC).json() == {"success": True})
    
    assert (leader1.put_message(TEST_TOPIC, TEST_MESSAGE).json()
            == {"success": True})

    leader1.commit_clean(ELECTION_TIMEOUT)
    leader2 = swarm.get_leader_loop(NUMBER_OF_LOOP_FOR_SEARCHING_LEADER)

    assert (leader2 != None)
    assert(leader2.get_message(TEST_TOPIC).json()
           == {"success": True, "message": TEST_MESSAGE})


########################## TOPIC TESTS ##########################
def test_get_topic_empty(node):
    assert(node.get_topics().json() == {"success": True, "topics": []})


def test_create_topic(node):
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})


def test_create_different_topics(node):
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})
    assert(node.create_topic("test_topic_different").json()
           == {"success": True})


def test_create_same_topic(node):
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})
    assert(node.create_topic(TEST_TOPIC).json() == {"success": False})


def test_get_topic(node):
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})
    assert(node.get_topics().json() == {
           "success": True, "topics": [TEST_TOPIC]})


def test_get_same_topic(node):
    assert(node.create_topic(TEST_TOPIC).json() == {"success": True})
    assert(node.create_topic(TEST_TOPIC).json() == {"success": False})
    assert(node.get_topics().json() == {
           "success": True, "topics": [TEST_TOPIC]})


def test_get_multiple_topics(node):
    topics = []
    for i in range(5):
        topic = TEST_TOPIC + str(i)
        assert(node.create_topic(topic).json() == {"success": True})
        topics.append(topic)
    assert(node.get_topics().json() == {
           "success": True, "topics": topics})


def test_get_multiple_topics_with_duplicates(node):
    topics = []
    for i in range(5):
        topic = TEST_TOPIC + str(i)
        assert(node.create_topic(topic).json() == {"success": True})
        assert(node.create_topic(topic).json() == {"success": False})
        topics.append(topic)
    assert(node.get_topics().json() == {
           "success": True, "topics": topics})


########################## MESSAGE TEST ##########################


def test_get_message_from_inexistent_topic(node_with_test_topic):
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": False})


def test_get_message(node_with_test_topic):
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": False})


def test_put_message(node_with_test_topic):
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})


def test_put_and_get_message(node_with_test_topic):
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})


def test_put2_and_get1_message(node_with_test_topic):
    second_message = TEST_MESSAGE + "2"
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, second_message).json() == {"success": True})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})


def test_put2_and_get2_message(node_with_test_topic):
    second_message = TEST_MESSAGE + "2"
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, second_message).json() == {"success": True})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": second_message})


def test_put2_and_get3_message(node_with_test_topic):
    second_message = TEST_MESSAGE + "2"
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, TEST_MESSAGE).json() == {"success": True})
    assert(node_with_test_topic.put_message(
        TEST_TOPIC, second_message).json() == {"success": True})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": TEST_MESSAGE})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": True, "message": second_message})
    assert(node_with_test_topic.get_message(
        TEST_TOPIC).json() == {"success": False})

