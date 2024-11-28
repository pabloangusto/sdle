import pdb

class ShoppingList:

    def __init__(self):
        self.id = 0
        self.list = 0
        self.vector_clock = {}
        self.items = {}


    def set_vector_clock(self, dictionary):
        self.vector_clock = dictionary

    def get_vector_clock(self):
        return self.vector_clock
    
    def increment_clock(self):
        self.vector_clock[self.id] = self.vector_clock.get(self.id, 0) + 1
        print("vc", self.vector_clock)
        return self.vector_clock[self.id]
    
    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_list(self):
        return self.list

    def set_list(self, list):
        self.list = list
    
    def get_items(self):
        return self.items
    
    def set_items(self, items):
        self.items = items
    
    
    def is_empty(self):
        return len(self.items) == 0
    

    def add_item(self, name, item):
        timestamp = self.increment_clock()

        if name not in self.items:  
            self.items[name] = {
                "quantity": item["quantity"],
                "acquired": item["acquired"],
                "timestamp": timestamp
            }

        return timestamp
    
    def delete_item(self, name):
        if name in self.items:
            timestamp = self.increment_clock()
            del self.items[name]
            print("Item deleted")
            return timestamp
        else:
            raise ValueError("Item does not exist in the shopping list.")

    def item_acquired(self, name):
        if name in self.items:
            timestamp = self.increment_clock()
            self.items[name]["acquired"] = True
            self.items[name]["timestamp"] = timestamp
            return timestamp
        else:
            raise ValueError("Item does not exist in the shopping list.")

    def item_not_acquired(self, name):
        if name in self.items:
            timestamp = self.increment_clock()
            self.items[name]["acquired"] = False
            self.items[name]["timestamp"] = timestamp
            return timestamp
        else:
            raise ValueError("Item does not exist in the shopping list.")

    def increment_quantity(self, name):
        if name in self.items:

            timestamp = max(self.increment_clock(), int(self.items[name]["timestamp"])) + 1
            updated_quantity = int(self.items[name]["quantity"]) + 1

            self.items[name]["quantity"] = updated_quantity
            self.items[name]["timestamp"] = timestamp

            print("Increment quantity")

            print(self.items[name]["timestamp"])

            return timestamp
    
    def decrement_quantity(self, name):
        if name in self.items:
            timestamp = max(self.increment_clock(), int(self.items[name]["timestamp"])) +  1           
            updated_quantity = int(self.items[name]["quantity"]) - 1

            if updated_quantity == 0:
                del self.items[name]
            else:
                self.items[name]["quantity"] = updated_quantity
                self.items[name]["timestamp"] = timestamp

            return timestamp
        
    def encode(self):
        encoded_list = ""
        encoded_list += f"{self.list}:{self.id}\n"
        for key, value in self.vector_clock.items():
            encoded_list += f"{key},{value}:"
        encoded_list += "\n"
        for name, item in self.items.items():
            encoded_list += f"{name}:{item['quantity']}:{item['acquired']}:{item['timestamp']}\n"
        
        return encoded_list

    def decode(self, encoded_list):
        # pdb.set_trace()
        lines = encoded_list.split("\n")
        self.list = lines[0].split(":")[0]
        self.id = lines[0].split(":")[1]
        vector_clock = lines[1].split(":")
        for pair in vector_clock:
            if pair:
                key, value = pair.split(",")
                self.vector_clock[key] = int(value)
        for line in lines[2:]:
            if line:
                name, quantity, acquired, timestamp = line.split(":")
                self.items[name] = {
                    "quantity": quantity,
                    "acquired": acquired,
                    "timestamp": timestamp
                }

    def __str__(self):
        result = "\n> Shopping List Items:\n"
        for name, item in self.items.items():
            result += f" - Name: {name}, Quantity: {item['quantity']}, Acquired: {item['acquired']}, Timestamp: {item['timestamp']}\n"
        return result
    
    def merge(self, other):
        # pdb.set_trace()  # Punto de interrupción
        sucessor = False
        antecessor = False

        for id, clock in self.vector_clock.items():
            if id in other.get_vector_clock():
                if clock > other.get_vector_clock()[id]:
                    antecessor = True
                else:
                    sucessor = True
                    if antecessor:
                        break
            else:
                antecessor = True

        for id, clock in other.vector_clock.items():
            if id not in self.vector_clock:
                sucessor = True
                break

        # pdb.set_trace()  # Punto de interrupción
        if not antecessor and sucessor:
            self.set_vector_clock(other.get_vector_clock())
            self.set_items(other.get_items())
        elif antecessor and sucessor:
            for name, item in other.get_items().items():
                if name not in self.items or item["timestamp"] > self.items[name]["timestamp"]:
                    self.items[name] = item
            for id, clock in other.get_vector_clock().items():
                self.vector_clock[id] = max(self.vector_clock.get(id, 0), clock)
        return antecessor, sucessor

    

    
    
    
