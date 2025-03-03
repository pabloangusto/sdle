import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import zmq
from common.shoppingList import *
import hashlib
import threading
import time
import pdb
from os.path import dirname, abspath

server_local_lists = {}
parent_dir = dirname(dirname(abspath(__file__)))

N=2 # Length of preference list

VN=3 # Number of virtual nodes



def save_server_state(id):
    # Create directory if it doesn't exist
    os.makedirs(parent_dir + "/data/server", exist_ok=True)
    
    with open(parent_dir + "/data/server/"+str(id)+".json", "w") as f:
        json.dump({list_id: list_data.to_dict() for list_id, list_data in server_local_lists.items()}, f)

def load_server_state(id):
    try:
        with open(parent_dir + "/data/server/"+str(id)+".json", "r") as f:
            data = json.load(f)
            for list_id, list_data in data.items():
                server_local_lists[list_id] = ShoppingList()
                server_local_lists[list_id].from_dict(list_data)
    except Exception as e:
        return False
    return True

def hash_list_id(list_id):
    print("Hashing list id", int(hashlib.md5(list_id.encode()).hexdigest(), 16))
    return int(hashlib.md5(list_id.encode()).hexdigest(), 16)

def forward_request(preference_list, client_shopping_list, message_multipart):
    print("Forwarding request")
    context = zmq.Context()
    message = json.dumps(client_shopping_list.to_dict())
    
    for p in preference_list:
        
            socket = context.socket(zmq.REQ)
            socket.connect(f"tcp://localhost:{p}")
            print(f"Sending message to server: {p}")
            
            socket.send_multipart([message_multipart[0], b'', message.encode() ])
            socket.RCVTIMEO = 1000  # 1000 milliseconds = 1 second
            try:
                response = socket.recv()
                print(f"Received response: {response}")
                break
            except zmq.Again:
                print(f"No response from server {p} within the timeout period. Trying next node.")



def propagate_update(preference_list, response):
    print("Propagating update")
    replicated = 1
    while replicated < min(N, len(preference_list)):
        for p in preference_list:
            
            if p != port:
                context = zmq.Context()
                socket = context.socket(zmq.REQ)
                socket.connect(f"tcp://localhost:{p}")
                print(f"Sending message to server: {p} ")
                socket.send_string(response)
                socket.RCVTIMEO = 1000  # 1000 milliseconds = 1 second
                try:
                    ack = socket.recv()
                    print(f"Received ack from server {p}")
                    n_shopping_list = ShoppingList().from_dict(json.loads(ack))
                    if not server_local_lists[n_shopping_list.list].is_equal(n_shopping_list):
                        server_local_lists[n_shopping_list.list].merge(n_shopping_list)
                        replicated = 1
                except zmq.Again:
                    print(f"No ack from server {p} within the timeout period. Trying next node.")
                replicated += 1
                if replicated == N:
                    break
    save_server_state(id)


def request_received(socket, message_multipart):

    message = message_multipart[2]
    print("Received request")

    client_shopping_list = ShoppingList().from_dict(json.loads(message))
    hash_list = hash_list_id(client_shopping_list.list)
    hash_nodes = []
    for i in range(VN):
        for n in active_nodes:
            if i == 0:
                hash_nodes.append({'id': n['id'], 'port': n['port'], 'h': int(hashlib.md5(str(n['id']).encode()).hexdigest(), 16)})
            else:
                hash_nodes.append({'id': n['id'], 'port': n['port'], 'h': int(hashlib.md5((str(n['id']) + str(i)).encode()).hexdigest(), 16)})
     
    unique_ids = set()
    sorted_nodes = []
    for node in sorted(hash_nodes, key=lambda x: (x['h'] < hash_list, x['h'])):
        if node['id'] not in unique_ids:
            unique_ids.add(node['id'])
            sorted_nodes.append(node)
            if len(sorted_nodes) == N:
                break
    preference_list = []
    for n in sorted_nodes:
        preference_list.append(n['port'])
    print("Preference list: ", preference_list)
    if port in preference_list:
        if client_shopping_list.list not in server_local_lists:
            server_local_lists[client_shopping_list.list] = client_shopping_list
            response = server_local_lists[client_shopping_list.list].to_dict()
            print("Sending not changed message to client")
            propagate = threading.Thread(target=propagate_update, args=(preference_list, json.dumps(client_shopping_list.to_dict())))
            propagate.start()
            
            socket.send_multipart([message_multipart[0],b'', json.dumps(response).encode()])

        else:
            server_local_lists[client_shopping_list.list].merge(client_shopping_list)
            response = server_local_lists[client_shopping_list.list].to_dict()
            propagate = threading.Thread(target=propagate_update, args=(preference_list, json.dumps(response)))
            propagate.start()
            print("Sending message to client")
            socket.send_multipart([message_multipart[0],b'', json.dumps(response).encode()])

            print(server_local_lists[client_shopping_list.list])
    else:
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
                
                if(value['id'] == int(message.split(":")[0])):
                    previous = True
            if not previous:
                
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
        
        if len(message) == 1:
            
            client_shopping_list = ShoppingList().from_dict(json.loads(message[0].decode()))
            if client_shopping_list.list not in server_local_lists:
                server_local_lists[client_shopping_list.list] = client_shopping_list
            else:
                server_local_lists[client_shopping_list.list].merge(client_shopping_list)

            response = server_local_lists[client_shopping_list.list].to_dict()
            socket3.send_string(json.dumps(response))
            print(server_local_lists[client_shopping_list.list])
            save_server_state(id)


        else:
            socket3.send(b"ok")
            update_thread = threading.Thread(target=request_received, args=(socket, message))
            update_thread.start()

id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
port = 5500 + id

for i in range(VN):
    if i == 0:
        print("Hashing node id", int(hashlib.md5(str(id).encode()).hexdigest(), 16))
    else:
        print("Hashing node id", int(hashlib.md5((str(id) + str(i)).encode()).hexdigest(), 16))

active_nodes = []
active_nodes.append({"id": int(id), "port": int(port)})

load_server_state(id)

context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.connect("tcp://localhost:5560")
print("Server started")

update_thread = threading.Thread(target=seeds)
update_thread.start()

update_thread = threading.Thread(target=node_request)
update_thread.start()
while True:
    message = socket.recv_multipart()
    request_received(socket, message)


