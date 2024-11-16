import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import zmq
from common.utils import *
from common.shoppingList import *

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://localhost:5560")

active_lists = {}

def request_received(socket, message):
    print("Received request")

    client_shopping_list = ShoppingList()
    client_shopping_list.decode(message.decode())
    print(client_shopping_list)

    if client_shopping_list.list not in active_lists:
        active_lists[client_shopping_list.list] = client_shopping_list
        socket.send(b"Your list haven't changed.\n")

    else:

        active_lists[client_shopping_list.list].merge(client_shopping_list)
        socket.send(b"Your list have changed.\n")


    print(active_lists[client_shopping_list.list])



    
while True:
    message = socket.recv()
    print(f"Received request: {message}")
    request_received(socket, message)
