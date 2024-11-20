import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import zmq
from common.utils import *
from common.shoppingList import *
import hashlib
import threading
import time
import pdb

id = int(sys.argv[1])
port = 5500 + id
W = 2
R = 2


active_lists = {}
active_nodes = {}
active_nodes[str(id)] = str(port)

def hash_list_id(list_id):
    print("Hashing list id", hashlib.md5(list_id.encode()))
    return int(hashlib.md5(list_id.encode()).hexdigest(), 16)

def forward_request(id_node, client_shopping_list, message_multipart):
    print("Forwarding request")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://localhost:{5500+id_node}")
    message = client_shopping_list.encode()
    print("Sending message to server: " + str(id_node) + message )
    socket.send_multipart([message_multipart[0],b'', message.encode()])
    response = socket.recv_string()
    print(f"Received response: {response}")

def request_received(socket, message_multipart):

    message = message_multipart[2]
    print("Received request", message)

    client_shopping_list = ShoppingList()
    client_shopping_list.decode(message.decode())
    print(client_shopping_list)

    id_node = hash_list_id(client_shopping_list.list) % len(active_nodes)
    # pdb.set_trace()

    if id >= id_node and id < id_node + W:

        if client_shopping_list.list not in active_lists:
            active_lists[client_shopping_list.list] = client_shopping_list
            print("Sending not changed message to server")
            response = "Your list haven't changed.\n"
            socket.send_multipart([message_multipart[0],b'', response.encode()])

        else:

            active_lists[client_shopping_list.list].merge(client_shopping_list)
            response = active_lists[client_shopping_list.list].encode()
            print("Sending message to server: " + message)
            socket.send_multipart([message_multipart[0],b'', response.encode()])


        print(active_lists[client_shopping_list.list])
    else:
        print("Forwarding request")
        forward_request(id_node, client_shopping_list, message_multipart)



# def listen_for_updates():
#     print("Server listening")
#     context1 = zmq.Context()
#     socket1 = context1.socket(zmq.SUB)
#     socket1.connect("tcp://localhost:5569")
#     socket1.setsockopt_string(zmq.SUBSCRIBE, "all")
#     while True:
#         message = socket1.recv_string()
#         print(f"Received request: {message}")
        

# def send_updates():
#     print("Server sending")
#     context2 = zmq.Context()
#     socket2 = context2.socket(zmq.PUB)
#     socket2.connect("tcp://localhost:5570")
#     while True:
#         socket2.send_string(f"all {id} {port}")
#         time.sleep(4)
def seeds():
    context2 = zmq.Context()
    if id == 0:
        socket2 = context2.socket(zmq.REP)
        socket2.bind("tcp://*:5570")
        while True:
            message = socket2.recv_string()
            active_nodes[message.split(":")[0]] = message.split(":")[1]
            message = f"{id}:{port}\n"
            for key, value in active_nodes.items():
                message += f"{key}:{value}\n"
            socket2.send_string(message)
    else:
        socket2 = context2.socket(zmq.REQ)
        socket2.connect("tcp://localhost:5570")
        while True:
            socket2.send_string(f"{id}:{port}")
            message = socket2.recv_string()
            message = message.split("\n")
            for node in message:
                if node:
                    active_nodes[node.split(":")[0]] = node.split(":")[1]
            time.sleep(4)
            print(active_nodes)

def node_request():
    context3 = zmq.Context()
    socket3 = context3.socket(zmq.REP)
    socket3.bind("tcp://localhost:"+str(port))
    while True:
        print("Server node listening: " + str(port))
        message = socket3.recv_multipart()
        print(f"Received request: {message}")
        socket3.send(b"ok")
        update_thread = threading.Thread(target=request_received, args=(socket, message))
        update_thread.start()
        # request_received(socket, message)

context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.connect("tcp://localhost:5560")
print("Server started")
# update_thread = threading.Thread(target=send_updates)
# update_thread.start()
update_thread = threading.Thread(target=seeds)
update_thread.start()
# update_thread2 = threading.Thread(target=listen_for_updates)
# update_thread2.start()
update_thread = threading.Thread(target=node_request)
update_thread.start()
hash_list_id("test")
while True:
    message = socket.recv_multipart()
    print(f"Received request: {message}")
    request_received(socket, message)


