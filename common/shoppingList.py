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
        # pdb.set_trace()
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
class EWFlag(Generic[K]):
    def __init__(self, id: K = None, context: DotContext = None):
        self.id = id
        self.dk = DotKernel[bool]() if context is None else DotKernel[bool]()
        if context:
            self.dk.Context = context

    def context(self):
        return self.dk.Context

    def __str__(self):
        return f"EWFlag: {self.dk}"

    def read(self):
        return any(self.dk.Entries.values())

    def enable(self, id):
        self.dk = self.dk
        self.dk.removeAll()
        self.dk.add(id, True)
        return self

    def disable(self, id):
        self.dk = self.dk
        self.dk.removeAll()
        return self

    def reset(self):
        self.dk = DotKernel[bool]()
        return self

    def join(self, other):
        self.dk.merge(other.dk)

    def to_dict(self):
        return {
            "id": self.id,
            "dk": self.dk.to_dict()
        }

    def from_dict(self, data):
        self.id = data.get("id", None)
        self.dk.from_dict(data.get("dk", {}))
        return self

class CCounter(Generic[V, K]):
    def __init__(self, id: K = None, context: DotContext = None):
        self.id = id
        self.dk = DotKernel[V]() if context is None else DotKernel[V]()
        if context:
            self.dk.Context = context

    def context(self):
        return self.dk.Context

    def inc(self, id, val: V = 1):
        dots = set()
        base = 0
        # pdb.set_trace()
        for dot, value in self.dk.Entries.items():
            if dot[0] == id:
                base = max(base, value)
                dots.add(dot)
        for dot in dots:
            self.dk.merge(self.dk)
            del self.dk.Entries[dot]
        self.dk.add(id, base + val)

    def dec(self, id, val: V = 1):
        dots = set()
        base = 0
        # pdb.set_trace()
        for dot, value in self.dk.Entries.items():
            if dot[0] == id:
                base = max(base, value)
                dots.add(dot)
        for dot in dots:
            self.dk.merge(self.dk)
            del self.dk.Entries[dot]
        self.dk.add(id, base - val)

    def reset(self):
        r = CCounter(self.id)
        r.dk = DotKernel[V]()
        return r

    def read(self):
        return sum(value.read() if isinstance(value, CCounter) else value for value in self.dk.Entries.values())

    def join(self, other):
        self.dk.merge(other.dk)

    def __str__(self):
        return f"CausalCounter: {self.dk}"

    def to_dict(self):
        return {
            "id": self.id,
            "dk": self.dk.to_dict()
        }

    def from_dict(self, data):
        self.id = data.get("id", None)
        self.dk.from_dict(data.get("dk", {}))
        return self

class Item:
    def __init__(self, id):
        self.counter = CCounter(id=id)
        self.flag = EWFlag(id=id)

    def inc(self, id, val=1):
        self.counter.inc(id, val)

    def dec(self, id, val=1):
        self.counter.dec(id, val)

    def enable(self, id):
        self.flag = self.flag.enable(id)

    def disable(self, id):
        self.flag = self.flag.disable(id)

    def read_counter(self):
        return self.counter.read()

    def read_flag(self):
        return self.flag.read()
    def read(self):
        # pdb.set_trace()
        return {
            "counter": self.counter.read(),
            "flag": self.flag.read()
        }
    def to_dict(self):
        return {
            "counter": self.counter.to_dict(),
            "flag": self.flag.to_dict()
        }

    def from_dict(self, data):
        self.counter.from_dict(data.get("counter", {}))
        self.flag.from_dict(data.get("flag", {}))
        return self

    def merge(self, other):
        self.counter.join(other.counter)
        self.flag.join(other.flag)

class AWORMap(Generic[K, V]):
    def __init__(self):
        self.keys = AWORSet[K]()
        self.entries = dict()

    def value(self):
        return {k: v.read() for k, v in self.entries.items()}

    def add(self, r, key: K, value: V):
        # pdb.set_trace()
        self.keys.add(r, key)
        if key not in self.entries:
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
        for key in self.keys.value():
            if key in self.entries and key in other.entries:
                if r1 > r2:
                    entries[key] = self.entries[key]
                    entries[key].merge(other.entries[key])
                else:
                    entries[key] = other.entries[key]
                    entries[key].merge(self.entries[key])
            elif key in self.entries:
                entries[key] = self.entries[key]
            elif key in other.entries:
                entries[key] = other.entries[key]

        self.entries = entries

    def from_dict(self, data):
        self.keys.from_dict(data.get("keys", {}))
        self.entries = {k: Item(id=k).from_dict(v) for k, v in data.get("entries", {}).items()}
        return self
    
    def to_dict(self):
        return {
            "keys": self.keys.to_dict(),
            "entries": {k: v.to_dict() for k, v in self.entries.items()}
        }
    

class ShoppingList:

    def __init__(self):
        self.id = 0
        self.list = 0
        self.items = AWORMap[str, Item]()

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
        if name not in self.items.value():
            i = Item(id=self.id)
            i.counter.inc(self.id, item["quantity"])
            self.items.add(self.id, name, i)
        # pdb.set_trace()
        # self.items.entries[name].inc(item["quantity"])
    
    def delete_item(self, name):
        if name in self.items.value():
            self.items.rem(self.id, name)
        else:
            raise ValueError("Item does not exist in the shopping list.")

    def increment_quantity(self, name):
        if name in self.items.value():
            self.items.entries[name].inc(self.id)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

    def decrement_quantity(self, name):
        if name in self.items.value():
            self.items.entries[name].dec(self.id)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

    def acquire_item(self, name):
        if name in self.items.value():
            self.items.entries[name].enable(self.id)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

    def not_acquire_item(self, name):
        if name in self.items.value():
            self.items.entries[name].disable(self.id)
        else:
            raise ValueError(f"Item '{name}' does not exist in the shopping list.")

    def from_dict(self, data):
        self.id = data.get("id", 0)
        self.list = data.get("list", 0)
        self.items.from_dict(data.get("items", {}))
        return self

    def to_dict(self):
        return {
            "id": self.id,
            "list": self.list,
            "items": self.items.to_dict() 
        }
    
    def __str__(self):
        # pdb.set_trace()
        result = "\n> Shopping List Items:\n"
        for name, item in self.items.value().items():
            result += f" - Name: {name}, Quantity: {item["counter"]}, Acquired: {item["flag"]}\n"
        return result
    
    def merge(self, other):
        self.items.merge(self.id, other.items, other.id)


    
    
    
