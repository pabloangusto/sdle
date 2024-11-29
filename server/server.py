import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import zmq
from common.utils import *
from common.shoppingList import *
import hashlib
import threading
import time
import pdb

id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
port = 5500 + id


N=2 # Length of preference list

VN=3 # Number of virtual nodes

active_lists = {}
active_nodes = []
active_nodes.append({"id": int(id), "port": int(port)})

def hash_list_id(list_id):
    print("Hashing list id", hashlib.md5(list_id.encode()))
    return int(hashlib.md5(list_id.encode()).hexdigest(), 16)

def forward_request(preference_list, client_shopping_list, message_multipart):
    print("Forwarding request")
    context = zmq.Context()
    message = json.dumps(client_shopping_list.to_dict())
    # pdb.set_trace()
    for p in preference_list:
        # pdb.set_trace()
            socket = context.socket(zmq.REQ)
            socket.connect(f"tcp://localhost:{p}")
            print(f"Sending message to server: {p} {message}")
            socket.send_multipart([message_multipart[0], b'', message.encode() ])
            socket.RCVTIMEO = 1000  # 1000 milliseconds = 1 second
            try:
                response = socket.recv()
                print(f"Received response: {response}")
                break
            except zmq.Again:
                active_nodes.pop(str(p))
                print(f"No response from server {p} within the timeout period. Trying next node.")



def propagate_update(preference_list, response):
    print("Propagating update")
    replicated = 1
    while replicated != N:
        for p in preference_list:
            #pdb.set_trace()
            if p != port:
                context = zmq.Context()
                socket = context.socket(zmq.REQ)
                socket.connect(f"tcp://localhost:{p}")
                print(f"Sending message to server: {p} {response}")
                socket.send_string(response)
                socket.RCVTIMEO = 1000  # 1000 milliseconds = 1 second
                try:
                    ack = socket.recv()
                    n_shopping_list = ShoppingList().from_dict(json.loads(ack))
                    if active_lists[n_shopping_list.list].is_equal(n_shopping_list):
                        replicated += 1
                        print(f"Received ack from server {p}: {ack} {replicated}")
                        if replicated == N:
                            break
                    else:
                        active_lists[n_shopping_list.list].merge(n_shopping_list)
                        replicated = 2
                except zmq.Again:
                    print(f"No ack from server {p} within the timeout period. Trying next node.")
    print(f"EXITTTTTTT")

def request_received(socket, message_multipart):

    message = message_multipart[2]
    # print("Received request", message)

    client_shopping_list = ShoppingList().from_dict(json.loads(message))
    print(client_shopping_list)
    hash_list = hash_list_id(client_shopping_list.list)
    hash_nodes = []
    for i in range(VN):
        for n in active_nodes:
            if i == 0:
                hash_nodes.append({'id': n['id'], 'port': n['port'], 'h': int(hashlib.md5(str(n['id']).encode()).hexdigest(), 16)})
            else:
                hash_nodes.append({'id': n['id'], 'port': n['port'], 'h': int(hashlib.md5((str(n['id']) + str(i)).encode()).hexdigest(), 16)})
    # pdb.set_trace() 
    sorted_nodes = sorted(hash_nodes, key=lambda x: x['h'], reverse=True)
    top_nodes = [node for node in sorted_nodes if node['h'] > hash_list][:N]
    preference_list = []
    #pdb.set_trace()
    for n in top_nodes:
        preference_list.append(n['port'])
    # pdb.set_trace()
    print(preference_list)
    if port in preference_list:
        if client_shopping_list.list not in active_lists:
            active_lists[client_shopping_list.list] = client_shopping_list
            response = active_lists[client_shopping_list.list].to_dict()
            print("Sending not changed message to server")
            propagate_update(preference_list, json.dumps(client_shopping_list.to_dict()))
            # pdb.set_trace()
            socket.send_multipart([message_multipart[0],b'', json.dumps(response).encode()])

        else:
            active_lists[client_shopping_list.list].merge(client_shopping_list)
            response = active_lists[client_shopping_list.list].to_dict()
            propagate_update(preference_list, json.dumps(response))
            print("Sending message to server: " + json.dumps(response))
            socket.send_multipart([message_multipart[0],b'', json.dumps(response).encode()])

            print(active_lists[client_shopping_list.list])
    else:
        print("Forwarding request")
        forward_request(preference_list, client_shopping_list, message_multipart)



def seeds():
    context2 = zmq.Context()
    if id == 0:
        socket2 = context2.socket(zmq.REP)
        socket2.bind("tcp://*:5570")
        while True:
            message = socket2.recv_string()
            previous = False
            for value in active_nodes:
                # pdb.set_trace()
                if(value['id'] == int(message.split(":")[0])):
                    previous = True
            if not previous:
                # pdb.set_trace()
                active_nodes.append({"id": int(message.split(":")[0]), "port": int(message.split(":")[1])})
            message = ""
            for node in active_nodes:
                message += str(node['id']) + ":" + str(node['port']) + "\n"
            socket2.send_string(message)
    else:
        socket2 = context2.socket(zmq.REQ)
        socket2.connect("tcp://localhost:5570")
        while True:
            socket2.send_string(f"{id}:{port}")
            message = socket2.recv_string()
            message = message.split("\n")
            # pdb.set_trace()
            active_nodes.clear()
            for node in message:
                if node:
                    active_nodes.append({"id": int(node.split(":")[0]), "port": int(node.split(":")[1])})
            time.sleep(4)

def node_request():
    context3 = zmq.Context()
    socket3 = context3.socket(zmq.REP)
    socket3.bind("tcp://localhost:"+str(port))
    while True:
        message = socket3.recv_multipart()
        print(f"Received request: {message}")
        # pdb.set_trace()
        if len(message) == 1:
            
            client_shopping_list = ShoppingList().from_dict(json.loads(message[0].decode()))
            if client_shopping_list.list not in active_lists:
                active_lists[client_shopping_list.list] = client_shopping_list
            else:
                active_lists[client_shopping_list.list].merge(client_shopping_list)

            response = active_lists[client_shopping_list.list].to_dict()
            socket3.send_string(json.dumps(response))


        else:
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
while True:
    message = socket.recv_multipart()
    # print(f"Received request: {message}")
    request_received(socket, message)


