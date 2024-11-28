import pdb
from typing import TypeVar, Generic
import json

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Helpers:
    @staticmethod
    def upsert(k, v, fn, map):
        if k in map:
            map[k] = fn(map[k], v)
        else:
            map[k] = v
        return map

    @staticmethod
    def mergeOption(merge, a, b):
        if a is not None and b is not None:
            return merge(a, b)
        elif a is not None:
            return a
        elif b is not None:
            return b
        else:
            return None

class DotContext:
    def __init__(self):
        self.version_vector = {} # actor -> version
        self.dot_cloud = set() 

    def contains(self, r, n):
        return self.version_vector.get(r, 0) >= n or (r, n) in self.dot_cloud

    def compact(self):
        new_dot_cloud = set()

        for dot in sorted(self.dot_cloud):
            actor, version = dot
            max_version = self.version_vector.get(actor, 0)

            if version == max_version + 1:
                self.version_vector[actor] = version
            elif version > max_version:
                new_dot_cloud.add(dot)

        self.dot_cloud = new_dot_cloud
        return self

    def nextDot(self, r):
        self.version_vector[r] = self.version_vector.get(r, 0) + 1
        return (r, self.version_vector[r])

    def add(self, dot):
        self.dot_cloud.add(dot)

    def merge(self, other):
        for actor, version in other.version_vector.items():
            self.version_vector[actor] = max(self.version_vector.get(actor, 0), version)

        self.dot_cloud.update(other.dot_cloud)

        return self
    
    def from_dict(self, data):
        self.version_vector = data.get("version_vector", {})
        self.dot_cloud = set(tuple(dot) for dot in data.get("dot_cloud", set()))
        return self
    
    def to_dict(self):
        return {
            "version_vector": self.version_vector,
            "dot_cloud": [list(dot) for dot in self.dot_cloud]
        }

class DotKernel(Generic[T]):
    def __init__(self):
        self.Context = DotContext() #vector_version
        self.Entries = {}       #dot -> value

    def values(self):
        return list(self.Entries.values())

    def add(self, rep, v):
        dot = self.Context.nextDot(rep)
        self.Entries[dot] = v
        self.Context.add(dot)

    def remove(self, rep, v):
        for dot, v2 in list(self.Entries.items()):
            if v2 == v:
                del self.Entries[dot]
                self.Context.add(dot)
        self.Context.compact()

    def removeAll(self):
        for dot in list(self.Entries.keys()):
            self.Context.add(dot)
        self.Entries.clear()
        self.Context.compact()

    def merge(self, other):
        # pdb.set_trace()
        if self is other:  # Evita auto-merge (idempotente)
            return

        # Obtener iteradores ordenados para los dots de ambos kernels
        it_keys = iter(sorted(self.Entries.keys()))
        ito_keys = iter(sorted(other.Entries.keys()))

        it = next(it_keys, None)
        ito = next(ito_keys, None)

        while it is not None or ito is not None:
            if it is not None and (ito is None or it < ito):
                # Dot solo en `self`
                if other.Context.contains(*it):  # Si el otro conoce el dot, eliminar aquí
                    del self.Entries[it]
                it = next(it_keys, None)
            elif ito is not None and (it is None or ito < it):
                # Dot solo en `other`
                if not self.Context.contains(*ito):  # Si no lo conocemos, importar
                    self.Entries[ito] = other.Entries[ito]
                ito = next(ito_keys, None)
            elif it is not None and ito is not None:
                # Dot en ambos
                it = next(it_keys, None)
                ito = next(ito_keys, None)

        self.Context.merge(other.Context)

    def from_dict(self, data):
        self.Context.from_dict(data["context"])
        self.Entries = {eval(dot): v for dot, v in data.get("entries", {}).items()}
        return self
    
    def to_dict(self):
        return {
            "context": self.Context.to_dict(),
            "entries": {str(dot): v for dot, v in self.Entries.items()}
        }
class AWORSet(Generic[T]):
    def __init__(self):
        self.core = DotKernel[T]()
        self.delta = None

    def value(self):
        return set(self.core.values())

    def add(self, r, v):
        self.core.remove(r, v)
        self.core.add(r, v)

    def rem(self, r, v):
        self.core.remove(r, v)

    def merge(self, other):
        self.delta = Helpers.mergeOption(lambda a, b: a.merge(b), self.delta, other.delta)
        self.core.merge(other.core)

    def mergeDelta(self, delta):
        self.delta = Helpers.mergeOption(lambda a, b: a.merge(b), self.delta, delta)
        self.core.merge(delta)

    def split(self):
        return self, self.delta
    
    def from_dict(self, data):
        self.core.from_dict(data["core"])
        self.delta = data.get("delta", None)
        return self
    
    def to_dict(self):
        return {
            "core": self.core.to_dict(),
            "delta": self.delta
        }

class AWORMap(Generic[K, V]):
    def __init__(self):
        self.keys = AWORSet[K]()
        self.entries = dict()

    def value(self):
        return self.entries

    def add(self, r, key: K, value: V):
        self.keys.add(r, key)
        self.entries[key] = value
        return self

    def rem(self, r, key: K):
        self.keys.rem(r, key)
        if key in self.entries:
            del self.entries[key]
        return self

    def merge(self, r1, other, r2):
        self.keys.merge(other.keys)
        entries = dict()
        # pdb.set_trace()
        for key in self.keys.value():
            if key in self.entries and key in other.entries:
                entries[key] = self.entries[key] if r1 > r2 else other.entries[key]
            elif key in self.entries:
                entries[key] = self.entries[key]
            elif key in other.entries:
                entries[key] = other.entries[key]

        self.entries = entries

    def from_dict(self, data):
        self.keys.from_dict(data.get("keys", {}))
        self.entries = data.get("entries", {})
        return self
    
    def to_dict(self):
        return {
            "keys": self.keys.to_dict(),
            "entries": self.entries
        }

# class GCounter:
#     def __init__(self):
#         self.counters = {}

#     def inc(self, id, value = 1):
#         if id not in self.counters:
#             self.counters[id] = 0
#         self.counters[id] += value

#     def read(self):
#         return sum(self.counters.values())

#     def merge(self, other):
#         for replica, value in other.counters.items():
#             if replica in self.counters:
#                 self.counters[replica] = max(self.counters[replica], value)
#             else:
#                 self.counters[replica] = value

#     def __str__(self):
#         message = ""
#         for id, value in self.counters.items():
#             message += f"{id},{value}."
#         return message
    
#     def from_string(self, counter_str):
#         if counter_str:
#             for pair in counter_str.split("."):
#                 if pair:
#                     id, value = pair.split(",")
#                     self.counters[id] = int(value)

# class PNCounter:
#     def __init__(self):
#         self.increment_counter = GCounter()  
#         self.decrement_counter = GCounter() 
    
#     def assign(self, id, value):
#         for _ in range(value):
#             self.increment_counter.inc(id)
    
#     def increment(self, id, value = 1):
#         self.increment_counter.inc(id, value)

#     def decrement(self, id, value = 1):
#         if self.read() >= 1: 
#             self.decrement_counter.inc(id, value)

#     def read(self):
#         return self.increment_counter.read() - self.decrement_counter.read()

#     def merge(self, other):
#         self.increment_counter.merge(other.increment_counter)
#         self.decrement_counter.merge(other.decrement_counter)

#     def __str__(self):
#         return f"{self.increment_counter};{self.decrement_counter}"
    
#     def from_string(self, counter_str):
#         # pdb.set_trace()
#         increment_str, decrement_str = counter_str.split(";")
#         self.increment_counter.from_string(increment_str)
#         self.decrement_counter.from_string(decrement_str)
    
class ShoppingList:

    def __init__(self):
        self.id = 0
        self.list = 0
        self.items = AWORMap[str, dict]()

    
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
        return len(self.items.value()) == 0
    
    def is_equal(self, other):
        return self.items.to_dict() == other.items.to_dict()

    def add_item(self, name, item):
        item_data = {
            "quantity": item["quantity"],
        }
        self.items.add(self.id, name, item_data)
    
    def delete_item(self, name):
        if name in self.items.value():
            self.items.rem(self.id, name)
        else:
            raise ValueError("Item does not exist in the shopping list.")

    def item_acquired(self, name):
        if name in self.items:
            self.items[name]["acquired"] = True
            self.items[name]["timestamp"] = timestamp
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
        if name in self.items.value():
            pdb.set_trace()
            item = self.items.value()[name]
            item["quantity"] += 1
            self.items.add(self.id, name, item)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

    
    def decrement_quantity(self, name):
        if name in self.items.value():
            item = self.items.value()[name]
            item["quantity"] = max(item["quantity"] - 1, 0)
            self.items.add(self.id, name, item)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

        
    # def encode(self):
    #     encoded_list = ""
    #     encoded_list += f"{self.list}:{self.id}\n"
    #     for key, value in self.vector_clock.items():
    #         encoded_list += f"{key},{value}:"
    #     encoded_list += "\n"
    #     for name, item in self.items.items():
    #         encoded_list += f"{name}:{item['acquired']}:{item['timestamp']}:{item['quantity']}\n"
        
    #     return encoded_list

    # def decode(self, encoded_list):
    #     # pdb.set_trace()
    #     lines = encoded_list.split("\n")
    #     self.list = lines[0].split(":")[0]
    #     self.id = lines[0].split(":")[1]
    #     vector_clock = lines[1].split(":")
    #     for pair in vector_clock:
    #         if pair:
    #             key, value = pair.split(",")
    #             self.vector_clock[key] = int(value)
    #     for line in lines[2:]:
    #         if line:
    #             name, acquired, timestamp, quantity = line.split(":")
    #             self.items[name] = {
    #                 "acquired": acquired,
    #                 "timestamp": timestamp,
    #                 "quantity": quantity
    #             }
    #             # pdb.set_trace()

    #     print("Decoded list", self)

    def from_dict(self, data):
        self.id = data.get("id", 0)
        self.list = data.get("list", 0)
        self.items.from_dict(data.get("items", {}))
        return self
    def to_dict(self):
        return {
            "id": self.id,
            "list": self.list,
            "items": self.items.to_dict()  # Convertimos los items a diccionario
        }
    
    def __str__(self):
        result = "\n> Shopping List Items:\n"
        for name, item in self.items.value().items():
            result += f" - Name: {name}, Counter: {item['quantity']}\n"
        return result
    
    def merge(self, other):
        self.items.merge(self.id, other.items, other.id)


    

    
    
    
