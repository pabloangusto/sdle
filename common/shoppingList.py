import pdb

class GCounter:
    def __init__(self):
        self.counters = {}

    def inc(self, id, value = 1):
        if id not in self.counters:
            self.counters[id] = 0
        self.counters[id] += value

    def read(self):
        return sum(self.counters.values())

    def merge(self, other):
        for replica, value in other.counters.items():
            if replica in self.counters:
                self.counters[replica] = max(self.counters[replica], value)
            else:
                self.counters[replica] = value

    def __str__(self):
        message = ""
        for id, value in self.counters.items():
            message += f"{id},{value}."
        return message
    
    def from_string(self, counter_str):
        if counter_str:
            for pair in counter_str.split("."):
                if pair:
                    id, value = pair.split(",")
                    self.counters[id] = int(value)

class PNCounter:
    def __init__(self):
        self.increment_counter = GCounter()  
        self.decrement_counter = GCounter() 
    
    def assign(self, id, value):
        for _ in range(value):
            self.increment_counter.inc(id)
    
    def increment(self, id, value = 1):
        self.increment_counter.inc(id, value)

    def decrement(self, id, value = 1):
        if self.read() >= 1: 
            self.decrement_counter.inc(id, value)

    def read(self):
        return self.increment_counter.read() - self.decrement_counter.read()

    def merge(self, other):
        self.increment_counter.merge(other.increment_counter)
        self.decrement_counter.merge(other.decrement_counter)

    def __str__(self):
        return f"{self.increment_counter};{self.decrement_counter}"
    
    def from_string(self, counter_str):
        # pdb.set_trace()
        increment_str, decrement_str = counter_str.split(";")
        self.increment_counter.from_string(increment_str)
        self.decrement_counter.from_string(decrement_str)
    



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
            counter = PNCounter() 
            counter.assign(self.id, item["quantity"])
            self.items[name] = {
                "acquired": item["acquired"],
                "timestamp": timestamp,
                "counter": counter
            }
            # pdb.set_trace()

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
            self.items[name]["counter"].increment(self.id)

            self.items[name]["timestamp"] = timestamp
            print("Increment quantity")

            print(self.items[name]["timestamp"])

            return timestamp
    
    def decrement_quantity(self, name):
        if name in self.items:
            timestamp = max(self.increment_clock(), int(self.items[name]["timestamp"])) +  1           
            self.items[name]["counter"].decrement(self.id)

            self.items[name]["timestamp"] = timestamp
            return timestamp
        
    def encode(self):
        encoded_list = ""
        encoded_list += f"{self.list}:{self.id}\n"
        for key, value in self.vector_clock.items():
            encoded_list += f"{key},{value}:"
        encoded_list += "\n"
        for name, item in self.items.items():
            encoded_list += f"{name}:{item['acquired']}:{item['timestamp']}:{item['counter']}\n"
        
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
                name, acquired, timestamp, counter = line.split(":")
                c = PNCounter()
                c.from_string(counter)
                self.items[name] = {
                    "acquired": acquired,
                    "timestamp": timestamp,
                    "counter": c
                }
                # pdb.set_trace()

        print("Decoded list", self)
    def __str__(self):
        result = "\n> Shopping List Items:\n"
        for name, item in self.items.items():
            result += f" - Name: {name}, Timestamp: {item['timestamp']}, Counter: {item['counter'].read()}\n"
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
            for name, item in other.items.items():
                if name not in self.items:
                    self.items[name] = item
                else:
                    # pdb.set_trace()
                    self.items[name]["aquired"] = item["acquired"]
                    self.items[name]["timestamp"] = item["timestamp"]
    
                    self.items[name]["counter"].merge(item["counter"])
                    # pdb.set_trace()
   
            for id, clock in other.get_vector_clock().items():
                self.vector_clock[id] = max(self.vector_clock.get(id, 0), clock)
        return antecessor, sucessor

    

    
    
    
