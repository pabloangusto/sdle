

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
        self.vector_clock[self.list] = self.vector_clock.get(self.list, 0) + 1
        return self.vector_clock[self.list]
    
    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_list(self):
        return self.list

    def set_list(self, list):
        self.list = list
    
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

            timestamp = self.increment_clock()
            updated_quantity = int(self.items[name]["quantity"]) + 1

            self.items[name]["quantity"] = updated_quantity
            self.items[name]["timestamp"] = timestamp

            print("Increment quantity")

            print(self.items[name]["timestamp"])

            return timestamp
    
    def decrement_quantity(self, name):
        if name in self.items:
            timestamp = self.increment_clock()
            updated_quantity = int(self.items[name]["quantity"]) - 1

            if updated_quantity == 0:
                del self.items[name]
            else:
                self.items[name]["quantity"] = updated_quantity
                self.items[name]["timestamp"] = timestamp

            return timestamp
        
    def encode(self):
        encoded_list = ""
        encoded_list += f"{self.list}\n"
        
        for name, item in self.items.items():
            encoded_list += f"{name}:{item['quantity']}:{item['acquired']}:{item['timestamp']}\n"
        
        return encoded_list

    def decode(self, encoded_list):
        lines = encoded_list.split("\n")
        self.list = lines[0]
        for line in lines[1:]:
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
    
    
    
