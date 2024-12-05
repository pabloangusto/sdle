import hashlib
import sys
import os
import json
from os.path import dirname, abspath
import zmq
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.shoppingList import *

parent_dir = dirname(dirname(abspath(__file__)))



def save_client_state(id):
    # Create directory if it doesn't exist
    os.makedirs(parent_dir + "/data/client", exist_ok=True)
    with open(parent_dir + "/data/client/"+id+".json", "w") as f:
        json.dump({list_id: list_data.to_dict() for list_id, list_data in client_local_lists.items()}, f)

def load_client_state(id):
    try:
        with open(parent_dir + "/data/client/"+id+".json", "r") as f:
            data = json.load(f)
            for list_id, list_data in data.items():
                client_local_lists[list_id] = ShoppingList()
                client_local_lists[list_id].from_dict(list_data)
    except Exception as e:
        print(f"Error loading state: {e}\n")
        return False
    return True

def show_menu(list_id):
    print(client_local_lists[list_id])

    print("\n Choose one action:")
    print(" 0 - Syncronize Shopping List")
    print(" 1 - Modify Shopping List")
    action = input("Action: ")   

    return action

def show_modifiers():
    print("\nChoose one option:")
    print(" 1 - Add item")
    print(" 2 - Delete item")
    print(" 3 - Item acquired")
    print(" 4 - Item not acquired")
    print(" 5 - Increment quantity")
    print(" 6 - Decrement quantity")
    operation = input("Option: ")
    return operation

def connect_to_server():
    try:
        #  Prepare our context and sockets
        # pdb.set_trace()
        context0 = zmq.Context()
        socket0 = context0.socket(zmq.REQ)
        socket0.connect("tcp://localhost:5559")
        return socket0
    except Exception as e:
        # Handle connection errors
        print(f"Error connecting to the server: {e}\n")
        return None




client_local_lists = {}


print("\nPlease enter your username. ")
user = input("> Username: ")

print("\nPlease enter listID. ")
list = input("> ListID: ")
print("Hashing list id", int(hashlib.md5(list.encode()).hexdigest(), 16))

load_client_state(user)

if list not in client_local_lists:
    shopping_list = ShoppingList()
    shopping_list.set_id(user)
    shopping_list.set_list(list)


    client_local_lists[list] = shopping_list



while True:

    # Show user list content
    operation = show_menu(list)
        
    # Modify Shopping List
    if operation == "1":

        operation = show_modifiers()

        # Add item
        match operation:
            case "1":
                item = {}
                name = input("\n> Enter item name: ")
                quantity = input("> Enter item quantity: ")

                try:
                    item["quantity"] = int(quantity)
                    item["acquired"] = False
                    client_local_lists[list].add_item(name, item)
                    print("\nItem added successfully.")

                except ValueError:
                    print("Quantity must be an integer.")

            case "2":
                print(client_local_lists[list])
                item_to_remove = input("\n> Enter the name of the item to remove: ")
                client_local_lists[list].delete_item(item_to_remove)
                print("\nItem removed successfully.")
            case "3":
                print(client_local_lists[list])
                item_acquired = input("\n> Enter the name of the item to mark as acquired: ")
                client_local_lists[list].acquire_item(item_acquired)
                print("\nItem marked as acquired successfully.")
            case "4":
                print(client_local_lists[list])
                item_acquired = input("\n> Enter the name of the item to mark as not aquired: ")
                client_local_lists[list].not_acquire_item(item_acquired)
                print("\nItem marked as not acquired successfully.")
            case "5":
                print(client_local_lists[list])
                item_to_increment = input("\n> Enter the name of the item to increment: ")
                client_local_lists[list].increment_quantity(item_to_increment)
                print("\nItem quantity incremented successfully.")
            case "6":
                print(client_local_lists[list])
                item_to_decrement = input("\n> Enter the name of the item to decrement: ")
                client_local_lists[list].decrement_quantity(item_to_decrement)
                print("\nItem quantity decremented successfully.")

    save_client_state(user)

    # Synchronize Shopping List
    socket = connect_to_server()
    print("Socket: ", socket)
    if socket is not None:
        try:
            # Send message to server
            # pdb.set_trace()
            message = json.dumps(client_local_lists[list].to_dict())
            print("Sending message to server: " + message)
            socket.send_string(message)
            
            # Set a timeout for receiving the response
            socket.RCVTIMEO = 1000  # 1000 milliseconds = 1 second
            
            try:
                response = socket.recv().decode()
                print("Message received from server")
                server_shopping_list = ShoppingList().from_dict(json.loads(response))
                client_local_lists[list].items = server_shopping_list.items
                save_client_state(user)


            except zmq.Again:
                print("No response from server within the timeout period.")
                socket.close()

        except Exception as e:
            print(f"Error sending message to the server: {e}\n")
            socket.close()

        
    

    

