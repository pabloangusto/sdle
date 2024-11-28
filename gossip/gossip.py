#!/usr/bin/env python3
import zmq

# Prepare our context and sockets
context = zmq.Context()
frontend = context.socket(zmq.XPUB)
backend = context.socket(zmq.XSUB)
frontend.bind("tcp://*:5569")
backend.bind("tcp://*:5570")

# Initialize poll set
poller = zmq.Poller()
poller.register(frontend, zmq.POLLIN)
poller.register(backend, zmq.POLLIN)

# Switch messages between sockets
while True:
    socks = dict(poller.poll())

    if socks.get(frontend) == zmq.POLLIN:
        message = frontend.recv_multipart()
        backend.send_multipart(message)
        print(f"Received request: {message}")   

    if socks.get(backend) == zmq.POLLIN:
        message = backend.recv_multipart()
        frontend.send_multipart(message)
        print(f"Received request: {message}")