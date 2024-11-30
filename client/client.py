import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import zmq
from common.utils import *
from common.shoppingList import *





# choose a list ID to connect
print("\nPlease enter your username. ")
user = input("> Username: ")
# choose a list ID to connect
print("\nPlease enter listID. ")
list = input("> ListID: ")

# Create ShoppingList object
shopping_list = ShoppingList()
shopping_list.set_id(user)
shopping_list.set_list(list)


client_local_lists[list] = shopping_list


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

while True:

    # Show user list content
    operation = show_menu(list)
        
    # Modify Shopping List
    if operation == "1":

        print("\nChoose one option:")
        print(" 1 - Add item")
        print(" 2 - Delete item")
        print(" 3 - Item acquired")
        print(" 4 - Item not acquired")
        print(" 5 - Increment quantity")
        print(" 6 - Decrement quantity")
        operation = input("Option: ")

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
                if client_local_lists[list].is_empty():
                    print("\nYou have no items to delete.\n")
                else:
                    print_items(list)
                    item_to_remove = input("\n> Enter the name of the item to remove: ")
                    client_local_lists[list].delete_item(item_to_remove)
                    print("\nItem removed successfully.")
            case "3":
                if client_local_lists[list].is_empty():
                    print("\nYou have no items to mark as acquired.\n")
                else:
                    print_items(list)
                    item_acquired = input("\n> Enter the name of the item to mark as acquired: ")
                    client_local_lists[list].acquire_item(item_acquired)
                    print("\nItem marked as acquired successfully.")
            case "4":
                if client_local_lists[list].is_empty():
                    print("\nYou have no items to mark as acquired.\n")
                else:
                    print_items(list)
                    item_acquired = input("\n> Enter the name of the item to mark as not aquired: ")
                    client_local_lists[list].not_acquire_item(item_acquired)
                    print("\nItem marked as not acquired successfully.")
            case "5":
                if client_local_lists[list].is_empty():
                    print("\nYou have no items to increment.\n")
                else:
                    print_items(list)
                    item_to_increment = input("\n> Enter the name of the item to increment: ")
                    client_local_lists[list].increment_quantity(item_to_increment)
                    print("\nItem quantity incremented successfully.")
            case "6":
                if client_local_lists[list].is_empty():
                    print("\nYou have no items to decrement.\n")
                else:
                    print_items(list)
                    item_to_decrement = input("\n> Enter the name of the item to decrement: ")
                    client_local_lists[list].decrement_quantity(item_to_decrement)
                    print("\nItem quantity decremented successfully.")

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

            except zmq.Again:
                print("No response from server within the timeout period.")
                socket.close()

        except Exception as e:
            print(f"Error sending message to the server: {e}\n")
            socket.close()

        
    

    

