"""
============================================================
03 - FUNCTIONAL PYTHON
============================================================
Python isn't a purely functional language, but it has
excellent functional tools. Decorators, generators, and the
itertools/functools libraries unlock a level of expressiveness
that makes your code read like a description of WHAT you want,
not HOW to get it.

These concepts appear constantly in Django and AI/ML code.
============================================================
"""

import functools
import itertools
import operator
from typing import TypeVar, Callable, Any, Generator, Iterator
from collections import defaultdict, Counter, OrderedDict, deque

T = TypeVar("T")
R = TypeVar("R")

# ─────────────────────────────────────────────────────────────
# DECORATORS — modify functions without touching them
# ─────────────────────────────────────────────────────────────
# A decorator is a function that takes a function and returns
# a (usually enhanced) function. Python's @ syntax is sugar for:
#   my_func = decorator(my_func)

def timer(func: Callable) -> Callable:
    """Measure how long a function takes."""
    @functools.wraps(func)    # preserves __name__, __doc__, etc.
    def wrapper(*args, **kwargs):
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"⏱  {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


def retry(max_attempts: int = 3, exceptions: tuple = (Exception,), delay: float = 1.0):
    """Retry a function on failure. A decorator FACTORY (returns a decorator)."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    print(f"Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def validate_types(**type_map):
    """Validate argument types at runtime."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            for param_name, expected_type in type_map.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"'{param_name}' must be {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_with_ttl(ttl_seconds: float = 60.0):
    """Cache results with a time-to-live."""
    import time
    def decorator(func: Callable) -> Callable:
        cache: dict = {}
        timestamps: dict = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            if key in cache and (now - timestamps[key]) < ttl_seconds:
                print(f"Cache hit for {func.__name__}")
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = now
            return result
        return wrapper
    return decorator


# Stacking decorators — applied bottom-up
@timer
@retry(max_attempts=3, exceptions=(ConnectionError,), delay=0.1)
def fetch_data(url: str) -> dict:
    """Fetch data from a URL (simulated)."""
    import random
    if random.random() < 0.3:  # 30% chance of failure
        raise ConnectionError(f"Failed to connect to {url}")
    return {"data": "some content", "url": url}


# Class-based decorator — useful for decorators with state
class rate_limiter:
    """Allow at most `calls` calls per `period` seconds."""

    def __init__(self, calls: int = 10, period: float = 1.0) -> None:
        self.calls = calls
        self.period = period
        self.call_times: deque = deque()

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            now = time.monotonic()
            # Remove calls older than the period
            while self.call_times and (now - self.call_times[0]) > self.period:
                self.call_times.popleft()
            if len(self.call_times) >= self.calls:
                raise RuntimeError(f"Rate limit exceeded: {self.calls} calls per {self.period}s")
            self.call_times.append(now)
            return func(*args, **kwargs)
        return wrapper


# ─────────────────────────────────────────────────────────────
# GENERATORS — lazy sequences, memory efficient
# ─────────────────────────────────────────────────────────────
# A generator function uses `yield` instead of `return`.
# It produces values ONE AT A TIME — perfect for large datasets.
# The function's state is preserved between yields.

def fibonacci() -> Generator[int, None, None]:
    """Infinite Fibonacci sequence — only computes what you ask for."""
    a, b = 0, 1
    while True:           # infinite, but lazy!
        yield a
        a, b = b, a + b


def read_large_file(filepath: str) -> Generator[str, None, None]:
    """Read a file line by line — never loads the whole file into memory."""
    with open(filepath) as f:
        for line in f:
            yield line.rstrip("\n")


def paginate(items: list, page_size: int) -> Generator[list, None, None]:
    """Yield chunks of a list."""
    for i in range(0, len(items), page_size):
        yield items[i:i + page_size]


def pipeline(*generators):
    """Chain generators into a processing pipeline."""
    return functools.reduce(lambda a, b: b(a), generators)


# Generator pipelines — compose lazy transformations
def numbers(start: int = 0) -> Generator[int, None, None]:
    n = start
    while True:
        yield n
        n += 1

def take(n: int) -> Callable:
    def _take(iterable) -> Generator:
        for i, item in enumerate(iterable):
            if i >= n:
                return
            yield item
    return _take

def where(predicate: Callable) -> Callable:
    def _where(iterable) -> Generator:
        for item in iterable:
            if predicate(item):
                yield item
    return _where

def select(transform: Callable) -> Callable:
    def _select(iterable) -> Generator:
        for item in iterable:
            yield transform(item)
    return _where

# Usage: first 5 even squares starting from 0
result = list(pipeline(
    numbers(),
    where(lambda x: x % 2 == 0),
    select(lambda x: x ** 2),
    take(5),
))
# [0, 4, 16, 36, 64]

# Generator expressions — like list comps, but lazy
squares_gen = (x**2 for x in range(1_000_000))  # no memory used yet
first_ten = list(itertools.islice(squares_gen, 10))  # only compute 10

# send() — two-way communication with generators
def running_average() -> Generator[float, float, None]:
    """Receives values via send(), yields running average."""
    total = 0.0
    count = 0
    while True:
        value = yield (total / count if count else 0.0)
        total += value
        count += 1

avg = running_average()
next(avg)           # prime the generator
avg.send(10)        # → 10.0
avg.send(20)        # → 15.0
result = avg.send(30)  # → 20.0
print(f"Running average: {result}")


# ─────────────────────────────────────────────────────────────
# ITERTOOLS — the generator toolkit
# ─────────────────────────────────────────────────────────────

def itertools_examples():
    # Infinite iterators
    counter = itertools.count(start=1, step=2)    # 1, 3, 5, 7, ...
    cycler  = itertools.cycle(["A", "B", "C"])    # A, B, C, A, B, C, ...
    repeater = itertools.repeat("hello", 3)        # hello, hello, hello

    # Finite iterators
    print(list(itertools.chain([1,2], [3,4], [5])))     # [1,2,3,4,5]
    print(list(itertools.chain.from_iterable([[1,2],[3,4]]))) # [1,2,3,4]
    print(list(itertools.islice(counter, 5)))             # [1,3,5,7,9]
    print(list(itertools.takewhile(lambda x: x < 5, [1,2,3,6,4])))  # [1,2,3]
    print(list(itertools.dropwhile(lambda x: x < 5, [1,2,3,6,4])))  # [6,4]
    print(list(itertools.compress("ABCDEF", [1,0,1,0,1,1])))  # ['A','C','E','F']
    print(list(itertools.pairwise([1,2,3,4])))            # [(1,2),(2,3),(3,4)]

    # Combinatorics
    print(list(itertools.permutations("ABC", 2)))  # all 2-length orderings
    print(list(itertools.combinations("ABC", 2)))  # all 2-length subsets
    print(list(itertools.combinations_with_replacement("AB", 2)))  # [('A','A'),('A','B'),('B','B')]
    print(list(itertools.product("AB", repeat=2)))  # cartesian product

    # groupby — group consecutive elements with the same key
    data = [
        {"city": "NYC", "name": "Alice"},
        {"city": "NYC", "name": "Bob"},
        {"city": "LA",  "name": "Carol"},
        {"city": "LA",  "name": "Dave"},
    ]
    # IMPORTANT: data must be sorted by key first!
    data.sort(key=lambda x: x["city"])
    for city, group in itertools.groupby(data, key=lambda x: x["city"]):
        names = [p["name"] for p in group]
        print(f"{city}: {names}")

    # accumulate — running totals
    values = [1, 2, 3, 4, 5]
    running_sum = list(itertools.accumulate(values))               # [1,3,6,10,15]
    running_product = list(itertools.accumulate(values, operator.mul))  # [1,2,6,24,120]
    print(running_sum, running_product)


# ─────────────────────────────────────────────────────────────
# FUNCTOOLS — higher-order function tools
# ─────────────────────────────────────────────────────────────

def functools_examples():
    # functools.lru_cache — memoize (cache) function results
    @functools.lru_cache(maxsize=None)  # unlimited cache size
    def fibonacci_cached(n: int) -> int:
        if n < 2:
            return n
        return fibonacci_cached(n - 1) + fibonacci_cached(n - 2)

    print(fibonacci_cached(50))   # instant — cached
    print(fibonacci_cached.cache_info())  # CacheInfo(hits=48, misses=51, ...)

    # functools.partial — "freeze" some arguments of a function
    def power(base: float, exponent: float) -> float:
        return base ** exponent

    square = functools.partial(power, exponent=2)
    cube   = functools.partial(power, exponent=3)
    print(square(5))   # 25.0
    print(cube(3))     # 27.0

    # Great for event handlers or callbacks
    import functools
    handlers = {
        "double": functools.partial(power, exponent=2),
        "triple": functools.partial(lambda x, n: x * n, n=3),
    }

    # functools.reduce — fold a sequence into a single value
    numbers = [1, 2, 3, 4, 5]
    product = functools.reduce(operator.mul, numbers, 1)  # 120
    print(product)

    # functools.singledispatch — function overloading by type
    @functools.singledispatch
    def process(value) -> str:
        return f"Unknown type: {type(value).__name__}"

    @process.register(int)
    def _(value: int) -> str:
        return f"Integer: {value * 2}"

    @process.register(str)
    def _(value: str) -> str:
        return f"String: {value.upper()}"

    @process.register(list)
    def _(value: list) -> str:
        return f"List with {len(value)} items"

    print(process(42))          # "Integer: 84"
    print(process("hello"))     # "String: HELLO"
    print(process([1,2,3]))     # "List with 3 items"
    print(process(3.14))        # "Unknown type: float"

    # functools.total_ordering — define __eq__ and ONE comparison, get the rest
    from functools import total_ordering

    @total_ordering
    class Temperature:
        def __init__(self, celsius: float) -> None:
            self.celsius = celsius

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Temperature):
                return NotImplemented
            return self.celsius == other.celsius

        def __lt__(self, other: Temperature) -> bool:
            return self.celsius < other.celsius

        # Python auto-generates: __le__, __gt__, __ge__

    temps = [Temperature(100), Temperature(0), Temperature(37)]
    print(min(temps).celsius)   # 0
    print(max(temps).celsius)   # 100
    print(sorted(temps, key=lambda t: t.celsius))


# ─────────────────────────────────────────────────────────────
# COLLECTIONS — the hidden gems of the standard library
# ─────────────────────────────────────────────────────────────

def collections_examples():
    # defaultdict — dict that never raises KeyError
    word_count: defaultdict[str, int] = defaultdict(int)
    for word in "the quick brown fox jumps over the lazy fox".split():
        word_count[word] += 1
    print(dict(word_count))

    graph: defaultdict[str, list] = defaultdict(list)
    graph["A"].append("B")
    graph["A"].append("C")
    graph["B"].append("D")

    # Counter — count hashable items
    letters = Counter("mississippi")
    print(letters)                        # Counter({'i': 4, 's': 4, 'p': 2, 'm': 1})
    print(letters.most_common(3))         # [('i', 4), ('s', 4), ('p', 2)]
    print(letters["i"])                   # 4
    print(letters["z"])                   # 0 — no KeyError!

    c1 = Counter(a=3, b=2)
    c2 = Counter(a=1, b=4)
    print(c1 + c2)   # Counter({'b': 6, 'a': 4})
    print(c1 - c2)   # Counter({'a': 2})
    print(c1 & c2)   # Counter({'a': 1, 'b': 2}) — min
    print(c1 | c2)   # Counter({'b': 4, 'a': 3}) — max

    # deque — double-ended queue, O(1) at both ends
    dq: deque[int] = deque([1, 2, 3], maxlen=5)
    dq.appendleft(0)    # add to left
    dq.append(4)        # add to right
    dq.popleft()        # remove from left
    dq.pop()            # remove from right
    dq.rotate(1)        # rotate right by 1

    # namedtuple — lightweight, immutable data holder
    from collections import namedtuple
    RGB = namedtuple("RGB", ["red", "green", "blue"])
    red = RGB(255, 0, 0)
    print(red.red, red.green, red.blue)  # 255 0 0
    print(red._asdict())                 # {'red': 255, 'green': 0, 'blue': 0}
    blue = red._replace(red=0, blue=255) # create modified copy


if __name__ == "__main__":
    print("=== Fibonacci (first 10) ===")
    fib = fibonacci()
    print([next(fib) for _ in range(10)])

    print("\n=== Paginate ===")
    data = list(range(1, 21))
    for page in paginate(data, 5):
        print(page)

    print("\n=== itertools examples ===")
    itertools_examples()

    print("\n=== functools examples ===")
    functools_examples()

    print("\n=== collections examples ===")
    collections_examples()
