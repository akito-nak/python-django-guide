"""
============================================================
04 - ADVANCED PYTHON
============================================================
This chapter covers the features that separate Python experts
from beginners: async programming, the full type system,
metaclasses, descriptors, and the import system.

These concepts appear heavily in Django async views, FastAPI,
and modern AI frameworks like LangChain.
============================================================
"""

import asyncio
import time
from typing import (
    TypeVar, Generic, Union, Optional, Literal, TypedDict,
    Annotated, get_type_hints, overload, TYPE_CHECKING
)
from typing import Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable

# ─────────────────────────────────────────────────────────────
# ASYNC / AWAIT — concurrent I/O without threads
# ─────────────────────────────────────────────────────────────
# Python is single-threaded. async/await doesn't use multiple
# threads — it uses cooperative multitasking. When one coroutine
# is waiting for I/O (network, disk), others can run.
#
# Perfect for: API calls, database queries, file I/O
# Not helpful for: CPU-heavy computation (use multiprocessing)

async def fetch_user(user_id: int) -> dict:
    """Simulates a database query."""
    await asyncio.sleep(0.1)  # simulate I/O wait
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_orders(user_id: int) -> list:
    """Simulates fetching orders from an API."""
    await asyncio.sleep(0.15)
    return [{"id": i, "user_id": user_id} for i in range(3)]

# Sequential — each awaits before the next starts
async def load_user_data_sequential(user_id: int) -> dict:
    start = time.perf_counter()
    user   = await fetch_user(user_id)      # wait 0.1s
    orders = await fetch_orders(user_id)    # then wait 0.15s — total: 0.25s
    elapsed = time.perf_counter() - start
    print(f"Sequential: {elapsed:.2f}s")
    return {**user, "orders": orders}

# Concurrent — both run "at the same time" (interleaved)
async def load_user_data_concurrent(user_id: int) -> dict:
    start = time.perf_counter()
    user, orders = await asyncio.gather(    # both start immediately
        fetch_user(user_id),                # 0.1s
        fetch_orders(user_id),              # 0.15s — total: ~0.15s (longest)
    )
    elapsed = time.perf_counter() - start
    print(f"Concurrent: {elapsed:.2f}s")
    return {**user, "orders": orders}

# asyncio.gather — run multiple coroutines concurrently
async def fetch_all_users(user_ids: list[int]) -> list[dict]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)

# asyncio.gather with error handling
async def fetch_all_safe(user_ids: list[int]) -> list[dict | None]:
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        r if not isinstance(r, Exception) else None
        for r in results
    ]

# Async context managers
class AsyncDatabaseConnection:
    async def __aenter__(self):
        await asyncio.sleep(0.01)  # simulate connect
        print("DB connected")
        return self

    async def __aexit__(self, *args):
        await asyncio.sleep(0.01)  # simulate disconnect
        print("DB disconnected")

    async def query(self, sql: str) -> list:
        await asyncio.sleep(0.05)
        return []

# Async generators — lazy streams of async data
async def stream_records(table: str):
    """Simulate streaming records from a database."""
    for i in range(5):
        await asyncio.sleep(0.01)  # simulate DB latency
        yield {"id": i, "table": table, "data": f"record_{i}"}

# Async comprehensions
async def async_comprehension_example():
    records = [record async for record in stream_records("users")]
    ids = [r["id"] async for r in stream_records("users") if r["id"] % 2 == 0]
    return records

# Timeouts and cancellation
async def with_timeout_example():
    try:
        result = await asyncio.wait_for(
            fetch_user(1),
            timeout=0.05  # 50ms timeout
        )
    except asyncio.TimeoutError:
        print("Request timed out!")
        result = None
    return result

# Task management
async def task_management():
    # Create tasks explicitly for more control
    task1 = asyncio.create_task(fetch_user(1), name="user-1")
    task2 = asyncio.create_task(fetch_user(2), name="user-2")

    # Wait for first completed (as_completed)
    for coro in asyncio.as_completed([fetch_user(3), fetch_user(4), fetch_user(5)]):
        result = await coro
        print(f"Got result: {result['id']}")

    # Cancel a task
    task1.cancel()
    try:
        await task1
    except asyncio.CancelledError:
        print("Task 1 was cancelled")


# ─────────────────────────────────────────────────────────────
# TYPE HINTS — advanced usage
# ─────────────────────────────────────────────────────────────

# TypeVar — generic type variable
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Generic classes
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("Stack is empty")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)


# TypedDict — type hints for dictionaries
class UserDict(TypedDict):
    id: int
    name: str
    email: str

class UserDictPartial(TypedDict, total=False):  # all fields optional
    name: str
    email: str

# Literal — restrict to specific values
Direction = Literal["north", "south", "east", "west"]
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

def move(direction: Direction, steps: int = 1) -> str:
    return f"Moving {direction} by {steps} steps"

# Annotated — add metadata to types (used by Pydantic, FastAPI, etc.)
from typing import Annotated

PositiveInt = Annotated[int, "must be > 0"]
Email = Annotated[str, "must contain @"]
Percentage = Annotated[float, "between 0.0 and 1.0"]

# Union / Optional patterns
def process(value: int | str | None) -> str:  # Python 3.10+ syntax
    match value:
        case None:
            return "nothing"
        case int(n):
            return f"integer: {n}"
        case str(s):
            return f"string: {s}"

# Function overloads — different signatures, one implementation
@overload
def double(x: int) -> int: ...
@overload
def double(x: str) -> str: ...
@overload
def double(x: list) -> list: ...

def double(x):  # type: ignore
    if isinstance(x, int):
        return x * 2
    elif isinstance(x, str):
        return x * 2
    elif isinstance(x, list):
        return x * 2


# ─────────────────────────────────────────────────────────────
# DESCRIPTORS — control attribute access
# ─────────────────────────────────────────────────────────────
# Descriptors power Python's property, classmethod, staticmethod,
# and are how Django model fields work under the hood.

class Validator:
    """A descriptor that validates values on assignment."""

    def __set_name__(self, owner, name: str) -> None:
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # accessed from class, not instance
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value) -> None:
        self.validate(value)
        setattr(obj, self.private_name, value)

    def validate(self, value) -> None:
        pass  # subclasses override


class PositiveNumber(Validator):
    def validate(self, value) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} must be a number")
        if value <= 0:
            raise ValueError(f"{self.name} must be positive, got {value}")


class NonEmptyString(Validator):
    def __init__(self, min_length: int = 1, max_length: int = 255) -> None:
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{self.name} must be a string")
        if len(value) < self.min_length:
            raise ValueError(f"{self.name} must be at least {self.min_length} chars")
        if len(value) > self.max_length:
            raise ValueError(f"{self.name} cannot exceed {self.max_length} chars")


class Product:
    name  = NonEmptyString(min_length=2, max_length=100)
    price = PositiveNumber()
    stock = PositiveNumber()

    def __init__(self, name: str, price: float, stock: int) -> None:
        self.name = name    # triggers NonEmptyString.__set__
        self.price = price  # triggers PositiveNumber.__set__
        self.stock = stock  # triggers PositiveNumber.__set__

# product = Product("", 10, 5)   # ❌ ValueError: name must be at least 2 chars
# product = Product("Shirt", -5, 5)  # ❌ ValueError: price must be positive


# ─────────────────────────────────────────────────────────────
# METACLASSES — classes of classes
# ─────────────────────────────────────────────────────────────
# A metaclass controls HOW classes are created.
# Django's ORM uses metaclasses to register models.
# You rarely need them — but understanding them demystifies frameworks.

class SingletonMeta(type):
    """Metaclass that enforces the Singleton pattern."""
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DatabasePool(metaclass=SingletonMeta):
    def __init__(self) -> None:
        print("Creating DatabasePool (only happens once)")
        self.pool_size = 10


class RegistryMeta(type):
    """Metaclass that auto-registers all subclasses."""
    _registry: dict[str, type] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # don't register the base class itself
            mcs._registry[name] = cls
            print(f"Registered: {name}")
        return cls

    @classmethod
    def get_registry(mcs) -> dict:
        return dict(mcs._registry)


class BaseHandler(metaclass=RegistryMeta):
    def handle(self, request: dict) -> dict: ...

class UserHandler(BaseHandler):     # auto-registered
    def handle(self, request: dict) -> dict:
        return {"handler": "user", "data": request}

class OrderHandler(BaseHandler):    # auto-registered
    def handle(self, request: dict) -> dict:
        return {"handler": "order", "data": request}


# ─────────────────────────────────────────────────────────────
# __slots__ — memory optimization
# ─────────────────────────────────────────────────────────────
# By default, Python stores instance attributes in a __dict__.
# __slots__ replaces that with a fixed array — uses less memory.
# Great for classes with MANY instances (e.g., data records).

class RegularPoint:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
    # stores attributes in self.__dict__ — flexible but uses more memory


class SlottedPoint:
    __slots__ = ("x", "y")  # no __dict__ — fixed attributes only

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
    # self.z = 1  # ❌ AttributeError — can't add new attributes
    # Uses ~40% less memory per instance — matters at scale


# ─────────────────────────────────────────────────────────────
# INTROSPECTION & DYNAMIC PROGRAMMING
# ─────────────────────────────────────────────────────────────

def introspection_examples():
    import inspect

    class MyClass:
        class_var = "shared"

        def __init__(self, x: int) -> None:
            self.x = x

        def method(self) -> int:
            return self.x * 2

    obj = MyClass(42)

    # Inspect an object
    print(dir(obj))                         # all attributes and methods
    print(vars(obj))                        # instance __dict__
    print(vars(MyClass))                    # class __dict__
    print(inspect.getmembers(obj, inspect.ismethod))  # all methods

    # Dynamic attribute access
    print(getattr(obj, "x"))                # 42
    print(getattr(obj, "y", "default"))     # "default" — no AttributeError
    setattr(obj, "y", 100)                  # set dynamically
    print(hasattr(obj, "y"))                # True
    delattr(obj, "y")                       # delete

    # Inspect function signatures
    def my_func(a: int, b: str = "hello", *, c: float) -> bool: ...
    sig = inspect.signature(my_func)
    for name, param in sig.parameters.items():
        print(f"{name}: {param.kind.name}, default={param.default}")

    # Type hints at runtime
    hints = get_type_hints(my_func)
    print(hints)  # {'a': int, 'b': str, 'c': float, 'return': bool}


if __name__ == "__main__":
    # Run async code
    asyncio.run(load_user_data_concurrent(1))
    asyncio.run(load_user_data_sequential(1))

    # Generic Stack
    stack: Stack[int] = Stack()
    stack.push(1)
    stack.push(2)
    print(f"Stack top: {stack.peek()}")

    # Descriptor validation
    product = Product("T-Shirt", 29.99, 100)
    print(f"Product: {product.name}, ${product.price}")

    # Singleton
    pool1 = DatabasePool()
    pool2 = DatabasePool()
    print(f"Same instance: {pool1 is pool2}")  # True

    introspection_examples()
