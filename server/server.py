#!/usr/bin/env python3
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

N=2

active_lists = {}
active_nodes = []
active_nodes.append({"id": int(id), "port": int(port)})

def hash_list_id(list_id):
    print("Hashing list id", hashlib.md5(list_id.encode()))
    return int(hashlib.md5(list_id.encode()).hexdigest(), 16)

def forward_request(preference_list, client_shopping_list, message_multipart):
    print("Forwarding request")
    context = zmq.Context()
    message = client_shopping_list.encode()
    # pdb.set_trace()
    for p in preference_list:
        # pdb.set_trace()
            socket = context.socket(zmq.REQ)
            socket.connect(f"tcp://localhost:{p}")
            print(f"Sending message to server: {p} {message}")
            socket.send_multipart([message_multipart[0], b'', message.encode()])
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
    replicated = 0
    while replicated != N:
        for p in preference_list:
            #pdb.set_trace()
            if p != port:
                context = zmq.Context()
                socket = context.socket(zmq.REQ)
                socket.connect(f"tcp://localhost:{p}")
                print(f"Sending message to server: {p} {response}")
                socket.send_string(response)
                socket.RCVTIMEO = 10000  # 1000 milliseconds = 1 second
                try:
                    ack = socket.recv()
                    if ack == b"ok":
                        print(f"Received ack from server {p}: {ack}")
                        replicated += 1
                        if replicated == N:
                            break
                    else:
                        n_shopping_list = ShoppingList()
                        n_shopping_list.decode(ack.decode())
                        active_lists[n_shopping_list.list].merge(n_shopping_list)
                        replicated = 2
                except zmq.Again:
                    print(f"No ack from server {p} within the timeout period. Trying next node.")

def request_received(socket, message_multipart):

    message = message_multipart[2]
    print("Received request", message)

    client_shopping_list = ShoppingList()
    client_shopping_list.decode(message.decode())
    print(client_shopping_list)

    id_node = hash_list_id(client_shopping_list.list) % len(active_nodes)
    preference_list = []
    #pdb.set_trace()
    for n in range(N):
        preference_list.append(active_nodes[(id_node + n) % len(active_nodes)]['port'])
    # pdb.set_trace()
    print(preference_list)
    if port in preference_list:
        if client_shopping_list.list not in active_lists:
            active_lists[client_shopping_list.list] = client_shopping_list
            print("Sending not changed message to server")
            propagate_update(preference_list, client_shopping_list.encode())
            response = "Your list haven't changed.\n"
            socket.send_multipart([message_multipart[0],b'', response.encode()])

        else:
            antecessor, sucessor = active_lists[client_shopping_list.list].merge(client_shopping_list)
            if not antecessor and sucessor:
                response = "Your list haven't changed.\n"
                socket.send_multipart([message_multipart[0],b'', response.encode()])
            else:
                response = active_lists[client_shopping_list.list].encode()
                propagate_update(preference_list, response)
                print("Sending message to server: " + response)
                socket.send_multipart([message_multipart[0],b'', response.encode()])

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
            
            client_shopping_list = ShoppingList()
            client_shopping_list.decode(message[0].decode())
            if client_shopping_list.list not in active_lists:
                active_lists[client_shopping_list.list] = client_shopping_list
                print(active_lists[client_shopping_list.list])
                socket3.send(b"ok")

            else:
                antecessor, sucessor = active_lists[client_shopping_list.list].merge(client_shopping_list)
                if antecessor and sucessor:
                    response = active_lists[client_shopping_list.list].encode()
                    print("Sending message to server: " + response)
                    socket3.send_string(response.encode())
                else:
                    print(active_lists[client_shopping_list.list])
                    socket3.send(b"ok")

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
    print(f"Received request: {message}")
    request_received(socket, message)


