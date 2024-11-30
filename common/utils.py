from os.path import dirname, abspath
import pdb
parent_dir = dirname(dirname(abspath(__file__)))



# ----------------------------- Data -----------------------------

# Local storage:
#  - is a dictionary used for local storage of shopping lists, (simulated as an in-memory data structure)
server_local_lists = {}
client_local_lists = {}


# Active shopping lists
active_lists = []


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

# def print_items(list_id):
#     print(f"\n> {list_id} Shopping List Items:")
#     # pdb.set_trace()
#     for name, item in client_local_lists[list_id].items.value().items():
#         print(f" - Name: {name}, Quantity: {item['quantity']}, Read Count: {item['ccounter'].read()}")

def print_items(list_id):
    print(f"\n> {list_id} Shopping List Items:")
    for name, item in client_local_lists[list_id].items.value().items():
            print(f" - Name: {name}, Quantity: {item["counter"]}, Acquired: {item["flag"]}")