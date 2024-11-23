import sys
import os

from shoppingList import *

def test_gcounter_increment():
    print("Test GCounter Increment")
    gcounter = GCounter()
    gcounter.inc("A", 3)
    gcounter.inc("B", 5)
    print(f"Expected: 8, Got: {gcounter.read()}")

def test_gcounter_merge():
    print("\nTest GCounter Merge")
    gcounter1 = GCounter()
    gcounter2 = GCounter()
    gcounter1.inc("A", 5)
    gcounter2.inc("A", 3)
    gcounter2.inc("B", 7)
    gcounter1.merge(gcounter2)
    print(f"Expected: 12 (5 from A, 7 from B), Got: {gcounter1.read()}")

def test_pncounter_increment_and_decrement():
    print("\nTest PNCounter Increment and Decrement")
    pncounter = PNCounter()
    pncounter.increment("A", 5)
    pncounter.decrement("A", 3)
    print(f"Expected: 2, Got: {pncounter.read()}")

def test_pncounter_no_negative():
    print("\nTest PNCounter No Negative")
    pncounter = PNCounter()
    pncounter.decrement("A", 3)  # No debería permitir valores negativos
    print(f"Expected: 0, Got: {pncounter.read()}")

def test_pncounter_merge():
    print("\nTest PNCounter Merge")
    pncounter1 = PNCounter()
    pncounter2 = PNCounter()
    pncounter1.increment("A", 4)
    pncounter2.increment("A", 2)
    pncounter2.decrement("B", 3)
    pncounter1.merge(pncounter2)
    print(f"Expected: 4 - 3 = 1, Got: {pncounter1.read()}")


test_gcounter_increment()
test_gcounter_merge()
test_pncounter_increment_and_decrement()
test_pncounter_no_negative()
test_pncounter_merge()
