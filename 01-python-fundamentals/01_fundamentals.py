"""
============================================================
01 - PYTHON FUNDAMENTALS
============================================================
Python's philosophy: code should be readable, elegant, and
expressive. "There should be one — and preferably only one —
obvious way to do it." — The Zen of Python

Run this file: python 01_fundamentals.py
Or explore interactively: python -i 01_fundamentals.py
============================================================
"""

import sys
from decimal import Decimal

# ─────────────────────────────────────────────────────────────
# VARIABLES & TYPES — dynamic, but not untyped
# ─────────────────────────────────────────────────────────────
# Python is dynamically typed — you don't declare types,
# but every object HAS a type. "Duck typing": if it walks
# like a duck and quacks like a duck, it's a duck.

name = "Akito"          # str
age = 35                # int
height = 5.11           # float
is_active = True        # bool (capital T/F — Python is case-sensitive!)
nothing = None          # NoneType — Python's null

# Check types at runtime
print(type(name))       # <class 'str'>
print(type(age))        # <class 'int'>
print(isinstance(age, int))   # True
print(isinstance(age, (int, float)))  # True — checks against tuple of types

# Type hints (Python 3.5+) — optional but HIGHLY recommended
# They don't enforce anything at runtime, but IDEs and tools like mypy use them
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

# ─────────────────────────────────────────────────────────────
# NUMBERS — no surprises (well, almost none)
# ─────────────────────────────────────────────────────────────

# Integers in Python have UNLIMITED precision — no overflow!
huge = 2 ** 100         # 1267650600228229401496703205376 — no problem
print(huge)

# Float pitfall (same as every language)
print(0.1 + 0.2)        # 0.30000000000000004 — IEEE 754

# For money: ALWAYS use Decimal
price = Decimal("9.99")
tax = Decimal("0.08")
total = price * (1 + tax)
print(total)            # 10.7892 — exact!

# Integer division
print(10 // 3)          # 3  — floor division (always returns int)
print(10 / 3)           # 3.3333... — true division (always returns float)
print(10 % 3)           # 1  — modulo
print(2 ** 10)          # 1024 — exponentiation

# Useful number functions
print(abs(-42))         # 42
print(round(3.14159, 2))  # 3.14
print(divmod(17, 5))    # (3, 2) — quotient AND remainder in one call

# ─────────────────────────────────────────────────────────────
# STRINGS — Python's superpower
# ─────────────────────────────────────────────────────────────

# Three quoting styles — all produce str
single = 'Hello'
double = "World"
multi  = """This spans
multiple lines
without escape characters"""

# f-strings (Python 3.6+) — the modern way, fast and readable
name = "Akito"
score = 98.5
print(f"Name: {name}, Score: {score:.2f}")   # Name: Akito, Score: 98.50
print(f"2 + 2 = {2 + 2}")                    # expressions work too
print(f"{name!r}")                            # !r = repr(), !s = str(), !a = ascii()
print(f"{name:>20}")                          # right-align in 20 chars
print(f"{1_000_000:,}")                       # 1,000,000 — number formatting

# Common string methods
s = "  Hello, World!  "
print(s.strip())            # "Hello, World!" — remove whitespace
print(s.lower())            # "  hello, world!  "
print(s.upper())            # "  HELLO, WORLD!  "
print(s.replace(",", ";"))  # "  Hello; World!  "
print(s.split(","))         # ['  Hello', ' World!  ']
print("py" in "python")     # True — membership test
print("python".startswith("py"))  # True
print("python".endswith("on"))    # True
print("ha".join(["bwa", "bwa"]))  # "bwahawabwa" — join with separator

# String is immutable — methods return NEW strings
original = "hello"
modified = original.upper()  # original unchanged
print(original)  # "hello"
print(modified)  # "HELLO"

# Slicing — [start:stop:step]
s = "Hello, World!"
print(s[0])      # 'H'
print(s[-1])     # '!'  — negative = from end
print(s[7:12])   # 'World'
print(s[:5])     # 'Hello'  — omit start = from beginning
print(s[7:])     # 'World!' — omit stop = to end
print(s[::-1])   # '!dlroW ,olleH' — reverse!

# ─────────────────────────────────────────────────────────────
# LISTS — ordered, mutable, heterogeneous
# ─────────────────────────────────────────────────────────────

fruits = ["apple", "banana", "cherry"]
fruits.append("date")           # add to end
fruits.insert(1, "blueberry")   # insert at index
fruits.remove("banana")         # remove by value
popped = fruits.pop()           # remove and return last (or fruits.pop(0) for first)
fruits.extend(["fig", "grape"]) # add multiple items

print(fruits)
print(len(fruits))              # length
print(fruits[0])                # first element
print(fruits[-1])               # last element
print(fruits[1:3])              # slice

# Sorting
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
numbers.sort()                          # in-place sort (modifies original)
sorted_nums = sorted(numbers)           # returns new sorted list
sorted_desc = sorted(numbers, reverse=True)
by_length = sorted(fruits, key=len)     # sort by string length

# List unpacking
first, *rest = [1, 2, 3, 4, 5]
print(first)    # 1
print(rest)     # [2, 3, 4, 5]

a, b, *_, last = [1, 2, 3, 4, 5]
print(a, b, last)  # 1 2 5

# ─────────────────────────────────────────────────────────────
# TUPLES — ordered, IMMUTABLE
# ─────────────────────────────────────────────────────────────
# Use tuples for data that shouldn't change: coordinates,
# RGB values, database rows, function return values.

point = (3, 4)
r, g, b = (255, 0, 128)     # tuple unpacking
single_item = (42,)          # NOTE: trailing comma makes it a tuple!
not_a_tuple = (42)           # This is just 42 in parentheses

# Named tuples — tuples with labels (great for readable code)
from collections import namedtuple
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(p.x, p.y)     # 3 4  — access by name
print(p[0], p[1])   # 3 4  — still works by index

# ─────────────────────────────────────────────────────────────
# DICTIONARIES — key-value pairs, ordered (Python 3.7+)
# ─────────────────────────────────────────────────────────────

user = {
    "name": "Akito",
    "age": 35,
    "email": "akito@example.com",
    "active": True,
}

# Access
print(user["name"])                     # "Akito"
print(user.get("phone", "N/A"))         # "N/A" — safe access with default
print("email" in user)                  # True — check key existence

# Modify
user["phone"] = "+1-555-0100"           # add/update
user.update({"age": 36, "city": "NYC"}) # update multiple at once
deleted = user.pop("phone")             # remove and return value

# Iterate
for key in user:                        # iterates over keys
    print(key)

for key, value in user.items():         # iterates over key-value pairs
    print(f"{key}: {value}")

keys   = list(user.keys())
values = list(user.values())
items  = list(user.items())             # list of (key, value) tuples

# Dict merging (Python 3.9+)
defaults = {"timeout": 30, "retries": 3}
config   = {"timeout": 60, "debug": True}
merged = defaults | config              # config values win
print(merged)  # {'timeout': 60, 'retries': 3, 'debug': True}

# ─────────────────────────────────────────────────────────────
# SETS — unordered, unique values
# ─────────────────────────────────────────────────────────────

fruits = {"apple", "banana", "cherry", "apple"}  # duplicate removed
print(fruits)   # {'apple', 'banana', 'cherry'} — order not guaranteed

fruits.add("date")
fruits.discard("banana")    # remove if present — no error if missing
# fruits.remove("banana")   # would raise KeyError

a = {1, 2, 3, 4, 5}
b = {3, 4, 5, 6, 7}
print(a & b)    # {3, 4, 5}       — intersection
print(a | b)    # {1,2,3,4,5,6,7} — union
print(a - b)    # {1, 2}          — difference
print(a ^ b)    # {1, 2, 6, 7}    — symmetric difference

# ─────────────────────────────────────────────────────────────
# COMPREHENSIONS — Python's most elegant feature
# ─────────────────────────────────────────────────────────────

# List comprehension: [expression for item in iterable if condition]
squares      = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]
flat         = [x for row in [[1,2],[3,4],[5,6]] for x in row]  # flatten

# Dict comprehension
word_lengths = {word: len(word) for word in ["python", "django", "ai"]}
# {'python': 6, 'django': 6, 'ai': 2}

inverted = {v: k for k, v in {"a": 1, "b": 2}.items()}
# {1: 'a', 2: 'b'}

# Set comprehension
unique_lengths = {len(word) for word in ["cat", "dog", "elephant", "ant"]}
# {3, 8} — unique lengths only

# Generator expression — like a list comp but lazy (no memory overhead)
total = sum(x**2 for x in range(1_000_000))  # computes without building a list!

# ─────────────────────────────────────────────────────────────
# CONTROL FLOW
# ─────────────────────────────────────────────────────────────

# if / elif / else
score = 85
grade = (
    "A" if score >= 90
    else "B" if score >= 80
    else "C" if score >= 70
    else "F"
)
print(grade)  # "B" — ternary-style chaining

# match statement (Python 3.10+) — like switch, but way more powerful
command = "quit"
match command:
    case "quit" | "exit" | "q":
        print("Goodbye!")
    case "help" | "h":
        print("Showing help...")
    case str(s) if s.startswith("go "):
        destination = s[3:]
        print(f"Going to {destination}")
    case _:
        print(f"Unknown command: {command}")

# match with data structures
point = (1, 0)
match point:
    case (0, 0):
        print("Origin")
    case (x, 0):
        print(f"On x-axis at {x}")
    case (0, y):
        print(f"On y-axis at {y}")
    case (x, y):
        print(f"At ({x}, {y})")

# for loops
for i in range(5):          # 0, 1, 2, 3, 4
    print(i, end=" ")

for i in range(2, 10, 2):   # 2, 4, 6, 8 — start, stop, step
    print(i, end=" ")

# enumerate — get index AND value
fruits = ["apple", "banana", "cherry"]
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}. {fruit}")

# zip — iterate multiple iterables in parallel
names  = ["Alice", "Bob", "Carol"]
scores = [95, 87, 92]
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# while with else (unusual Python feature)
n = 10
while n > 0:
    n -= 1
else:
    print("Loop completed normally")  # runs if loop didn't break

# ─────────────────────────────────────────────────────────────
# FUNCTIONS — first-class citizens in Python
# ─────────────────────────────────────────────────────────────

def greet(name: str, greeting: str = "Hello", *, loud: bool = False) -> str:
    """
    Greet someone.

    Args:
        name: The person's name
        greeting: The greeting to use (default: "Hello")
        loud: If True, return in uppercase (keyword-only after *)

    Returns:
        A greeting string
    """
    result = f"{greeting}, {name}!"
    return result.upper() if loud else result

print(greet("Akito"))                           # "Hello, Akito!"
print(greet("Akito", "Hey"))                    # "Hey, Akito!"
print(greet("Akito", loud=True))                # "HELLO, AKITO!"
# greet("Akito", True)  # ❌ loud is keyword-only (after *)

# *args and **kwargs
def flexible(*args, **kwargs):
    print(f"Positional: {args}")     # tuple
    print(f"Keyword:    {kwargs}")   # dict

flexible(1, 2, 3, name="Alice", age=30)

# Unpacking into function calls
def add(a, b, c):
    return a + b + c

nums = [1, 2, 3]
print(add(*nums))               # unpacks list into positional args

config = {"a": 1, "b": 2, "c": 3}
print(add(**config))            # unpacks dict into keyword args


# ─────────────────────────────────────────────────────────────
# EXCEPTION HANDLING
# ─────────────────────────────────────────────────────────────

def safe_divide(a: float, b: float) -> float:
    try:
        result = a / b
    except ZeroDivisionError:
        print("Cannot divide by zero!")
        return 0.0
    except TypeError as e:
        print(f"Wrong types: {e}")
        raise  # re-raise the same exception
    else:
        # runs ONLY if no exception was raised
        print(f"Success: {a} / {b} = {result}")
        return result
    finally:
        # ALWAYS runs — for cleanup (close files, release locks)
        print("safe_divide complete")

# Custom exceptions
class AppError(Exception):
    """Base exception for this application."""
    pass

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")

class NotFoundError(AppError):
    def __init__(self, resource: str, identifier):
        super().__init__(f"{resource} not found: {identifier}")

try:
    raise ValidationError("email", "Must contain @")
except ValidationError as e:
    print(f"Field: {e.field}, Message: {e.message}")
except AppError as e:
    print(f"App error: {e}")


if __name__ == "__main__":
    print("=== Python Fundamentals ===")
    print(greet("World"))
    safe_divide(10, 2)
    safe_divide(10, 0)
