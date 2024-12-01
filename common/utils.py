from os.path import dirname, abspath
import pdb
import json
import os
from common.shoppingList import ShoppingList
parent_dir = dirname(dirname(abspath(__file__)))



# ----------------------------- Data -----------------------------

# Local storage:
#  - is a dictionary used for local storage of shopping lists, (simulated as an in-memory data structure)
server_local_lists = {}
client_local_lists = {}



def print_user_list(list_id):
    if client_local_lists[list_id].is_empty():
        print("\nThe list is empty.")
    else:
        print_items(list_id)

def show_menu(list_id):
    print("\n---------------------------------")
    print_user_list(list_id)
    print("\n----------------------------------") 

    print("\n Choose one action:")
    print(" 1 - Modify Shopping List")
    print(" 0 - Syncronize Shopping List")
    action = input("Action: ")   

    return action

def print_items(list_id):
    print(f"\n> {list_id} Shopping List Items:")
    for name, item in client_local_lists[list_id].items.value().items():
            print(f" - Name: {name}, Quantity: {item["counter"]}, Acquired: {item["flag"]}")


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

def save_server_state(id):
    # Create directory if it doesn't exist
    os.makedirs(parent_dir + "/data/server", exist_ok=True)
    # pdb.set_trace()
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
        print(f"Error loading state: {e}\n")
        return False
    return True