import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import zmq
from common.utils import *
from common.shoppingList import *

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.connect("tcp://localhost:5560")

active_lists = []

def request_received(message):
    print("Received request")

    shopping_list_from_client = ShoppingList()
    shopping_list_from_client.decode(message.decode())
    print(shopping_list_from_client)


    
while True:
    message = socket.recv()
    print(f"Received request: {message}")
    request_received(message)
    socket.send_string("Request processed")  # Enviar una respuesta al cliente