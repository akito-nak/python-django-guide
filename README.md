# Python & Django: The Complete Guide
### From "What's a variable?" to AI-powered production APIs

> Python is the most popular language in the world right now, and for good reason: it reads like English, runs everywhere, and powers everything from Instagram to NASA simulations. Django is the framework that turns Python into a full-stack web powerhouse in hours, not days.
>
> This guide is for everyone — the complete beginner meeting Python for the first time, the JavaScript developer making the jump, and the experienced developer who wants a solid reference for Django's deeper features and the AI ecosystem that's transformed what's possible in Python.
>
> No fluff. Plenty of personality. Real examples that go somewhere.

---

## Table of Contents

1. [Repo Structure](#repo-structure)
2. [Getting Started](#getting-started)
3. [Chapter 1 — Python Fundamentals](#chapter-1--python-fundamentals)
4. [Chapter 2 — OOP in Python](#chapter-2--object-oriented-programming)
5. [Chapter 3 — Functional Python](#chapter-3--functional-python)
6. [Chapter 4 — Advanced Python](#chapter-4--advanced-python)
7. [Chapter 5 — Django Core](#chapter-5--django-core)
8. [Chapter 6 — Django Models & ORM](#chapter-6--django-models--orm)
9. [Chapter 7 — Views & URLs](#chapter-7--views--urls)
10. [Chapter 8 — Django REST Framework](#chapter-8--django-rest-framework)
11. [Chapter 9 — Auth & Security](#chapter-9--auth--security)
12. [Chapter 10 — Testing](#chapter-10--testing)
13. [Chapter 11 — AI/ML Fundamentals](#chapter-11--aiml-fundamentals)
14. [Chapter 12 — NLP, LLMs & RAG](#chapter-12--nlp-llms--rag)
15. [Chapter 13 — Real-World Patterns](#chapter-13--real-world-patterns)
16. [Chapter 14 — Deployment](#chapter-14--deployment)
17. [Quick Reference](#quick-reference)

---

## Repo Structure

```
python-django-guide/
│
├── 01-python-fundamentals/
│   └── 01_fundamentals.py      ← Types, strings, lists, dicts, sets, comprehensions, exceptions
│
├── 02-oop/
│   └── 02_oop.py               ← Classes, inheritance, dataclasses, protocols, mixins, context managers
│
├── 03-functional-python/
│   └── 03_functional.py        ← Decorators, generators, itertools, functools, collections
│
├── 04-advanced-python/
│   └── 04_advanced.py          ← Async/await, type hints, descriptors, metaclasses, __slots__
│
├── 05-django-core/
│   └── 05_django_core.py       ← Settings, middleware, URL routing, app config
│
├── 06-django-models/
│   └── 06_models.py            ← Entities, relationships, managers, QuerySet API, signals, migrations
│
├── 07-django-views-urls/
│   └── 07_views_urls.py        ← FBVs, CBVs, async views, URL patterns, mixins
│
├── 08-django-rest-framework/
│   └── 08_drf.py               ← Serializers, ViewSets, permissions, filters, pagination, routers
│
├── 09-django-auth-security/
│   └── 09_auth_security.py     ← JWT flow, custom backends, permissions, throttling, OWASP
│
├── 10-testing/
│   └── 10_testing.py           ← pytest, factory_boy, APIClient, mocking, coverage
│
├── 11-ai-ml-fundamentals/
│   └── 11_ai_ml.py             ← NumPy, Pandas, scikit-learn, ML pipeline, model evaluation
│
├── 12-ai-nlp-llms/
│   └── 12_ai_nlp_llms.py       ← OpenAI API, embeddings, RAG, LangChain, HuggingFace, prompt engineering
│
├── 13-real-world-patterns/
│   └── 13_patterns.py          ← Service layer, Celery, caching, repository pattern, feature flags
│
├── 14-deployment/
│   ├── 14_deployment.py        ← Dockerfile, docker-compose, GitHub Actions CI/CD, prod checklist
│   └── requirements/
│       ├── base.txt            ← Core production dependencies
│       ├── development.txt     ← Dev + testing tools
│       └── ai.txt              ← AI/ML dependencies
│
├── .gitignore                  ← Comprehensive Python/Django/AI gitignore
└── README.md                   ← This file — the complete tutorial
```

---

## Getting Started

### Prerequisites
- Python 3.12+ ([python.org](https://python.org) or `brew install python`)
- pip and venv (come with Python)
- PostgreSQL (for Django chapters) — `brew install postgresql` or use Docker

### Set Up Your Environment

```bash
# Clone or download this repo
git clone https://github.com/yourusername/python-django-guide.git
cd python-django-guide

# Create and activate a virtual environment
# ALWAYS use a venv — never install packages globally
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r 14-deployment/requirements/development.txt

# Run any chapter file
python 01-python-fundamentals/01_fundamentals.py
python 03-functional-python/03_functional.py
```

### Start a Django Project from Scratch

```bash
# Install Django
pip install django djangorestframework

# Create project and app
django-admin startproject myproject .
python manage.py startapp users

# Run development server
python manage.py runserver

# Open http://127.0.0.1:8000 — you have a working web server
```

---

## Chapter 1 — Python Fundamentals

> **File:** `01-python-fundamentals/01_fundamentals.py`

### Why Python Feels Different

Python was designed with a philosophy: *readability counts*. Code is read far more than it's written. Python takes this seriously — indentation enforces structure (no braces), naming is explicit, and there's almost always "one obvious way" to do something.

```python
# Python is expressive — read this like English:
active_users = [user for user in users if user.is_active]
total = sum(order.total for order in orders)
first_admin = next((u for u in users if u.is_staff), None)
```

### The Type System

Python is **dynamically typed** — you don't declare types, but every value *has* a type. The interpreter knows `42` is an `int` and `"hello"` is a `str`. You can't accidentally mix them without Python telling you.

```python
age = 30            # int
name = "Akito"      # str
score = 98.5        # float
active = True       # bool (capital T and F — Python is case-sensitive)
nothing = None      # NoneType — Python's null
```

**Type hints** (Python 3.5+) are optional annotations that IDEs and tools use without affecting runtime:
```python
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times
```

### The Pitfalls Every Python Dev Hits

**1. Mutable default arguments — the most common bug for beginners**
```python
# ❌ WRONG — the list is created ONCE and shared across all calls
def add_item(item, cart=[]):
    cart.append(item)
    return cart

add_item("apple")   # ["apple"]
add_item("banana")  # ["apple", "banana"] — WHAT?

# ✅ RIGHT — use None as default, create inside the function
def add_item(item, cart=None):
    if cart is None:
        cart = []
    cart.append(item)
    return cart
```

**2. `is` vs `==`**
```python
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)   # True  — same values
print(a is b)   # False — different objects in memory

# `is` only makes sense for None, True, False, and small integers (cached by CPython)
if user is None:   # ✅ correct
if user == None:   # ⚠️ works but wrong idiom
```

**3. Integer division vs float division**
```python
print(10 / 3)   # 3.3333... — always float
print(10 // 3)  # 3          — floor division, always int
print(-7 // 2)  # -4         — floors toward negative infinity! (-3.5 → -4)
```

### f-Strings — Learn These First, Use Them Always

```python
name = "Alice"
score = 98.567

# Basic
print(f"Hello, {name}!")                    # Hello, Alice!

# Expressions inside braces
print(f"2 + 2 = {2 + 2}")                  # 2 + 2 = 4

# Format specs
print(f"Score: {score:.2f}")                # Score: 98.57
print(f"Score: {score:>10.2f}")             # Score:      98.57 (right-aligned in 10 chars)
print(f"{1_000_000:,}")                     # 1,000,000 (thousands separator)
print(f"{0.854:.1%}")                       # 85.4% (as percentage)

# Debug format (Python 3.8+) — shows name AND value
x = 42
print(f"{x=}")                              # x=42
```

### Comprehensions — Python's Most Powerful Feature

List comprehensions transform data without boilerplate loops:

```python
# Traditional loop:
squares = []
for x in range(10):
    if x % 2 == 0:
        squares.append(x ** 2)

# List comprehension — same thing, one line, reads like math:
squares = [x**2 for x in range(10) if x % 2 == 0]  # [0, 4, 16, 36, 64]

# Dict comprehension
word_lengths = {word: len(word) for word in ["python", "django", "ai"]}
# {'python': 6, 'django': 6, 'ai': 2}

# Generator expression — lazy (no memory allocated until needed):
total = sum(x**2 for x in range(1_000_000))   # handles 1M items with minimal memory
```

### The match Statement (Python 3.10+)

Python's `match` is not your grandfather's switch statement — it does structural pattern matching:

```python
match command:
    case "quit" | "exit":
        print("Goodbye!")
    case str(s) if s.startswith("go "):
        print(f"Going to {s[3:]}")
    case _:
        print("Unknown command")

# Match on data structures:
match point:
    case (0, 0):    print("Origin")
    case (x, 0):    print(f"On x-axis at {x}")
    case (0, y):    print(f"On y-axis at {y}")
    case (x, y):    print(f"At ({x}, {y})")
```

---

## Chapter 2 — Object-Oriented Programming

> **File:** `02-oop/02_oop.py`

### Classes: Not Just Containers for Methods

```python
class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0.0) -> None:
        self._owner = owner
        self.__balance = initial_balance  # __ = name mangled, harder to access outside

    @property
    def balance(self) -> float:
        return self.__balance             # read-only — no setter

    def deposit(self, amount: float) -> "BankAccount":
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.__balance += amount
        return self   # ← return self enables method chaining!

# account.deposit(100).deposit(200).deposit(50) — fluent API
```

### Dunder Methods — Making Your Objects Feel Native

"Dunder" = double underscore. These methods let your objects respond to built-in operations:

```python
class Vector:
    def __init__(self, x, y): self.x, self.y = x, y
    def __repr__(self):  return f"Vector({self.x}, {self.y})"     # repr()
    def __str__(self):   return f"({self.x}, {self.y})"           # str(), print()
    def __add__(self, o): return Vector(self.x+o.x, self.y+o.y)   # v1 + v2
    def __mul__(self, n): return Vector(self.x*n, self.y*n)        # v * 3
    def __len__(self):   return 2                                   # len(v)
    def __eq__(self, o): return self.x==o.x and self.y==o.y        # v1 == v2
    def __iter__(self):  return iter((self.x, self.y))             # for x in v
    def __bool__(self):  return bool(self.x or self.y)             # if v:

v1, v2 = Vector(1, 2), Vector(3, 4)
print(v1 + v2)      # Vector(4, 6)
x, y = v1           # unpacking works because of __iter__
```

### Dataclasses — The Right Tool for Data

```python
from dataclasses import dataclass, field

@dataclass
class User:
    name: str
    email: str
    age: int
    tags: list[str] = field(default_factory=list)  # ⚠️ mutable defaults need field()

    def __post_init__(self):   # validation after auto-generated __init__
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
        self.email = self.email.lower()

@dataclass(frozen=True)   # immutable — like a named tuple with type hints
class Point:
    x: float
    y: float

@dataclass(order=True)    # auto-generates < > <= >= from field order
class Version:
    major: int
    minor: int
    patch: int
```

Dataclasses auto-generate `__init__`, `__repr__`, and `__eq__`. Use them for anything that's "just data."

### Protocols — Duck Typing with Types

A Protocol says "I don't care what *type* you are — I care that you have these *methods*." No inheritance required:

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> str: ...
    def resize(self, factor: float) -> None: ...

# Neither of these inherit from Drawable — they just have the right methods:
class SVGCircle:
    def draw(self) -> str: return "<circle/>"
    def resize(self, factor: float) -> None: self.radius *= factor

class PNGImage:
    def draw(self) -> str: return "[PNG image]"
    def resize(self, factor: float) -> None: ...

# This function accepts EITHER because both satisfy the Drawable protocol:
def render_all(drawables: list[Drawable]) -> list[str]:
    return [d.draw() for d in drawables]
```

This is how Python achieves polymorphism without forcing an inheritance hierarchy.

---

## Chapter 3 — Functional Python

> **File:** `03-functional-python/03_functional.py`

### Decorators — The Most Useful Pattern in Python

A decorator wraps a function to add behaviour without changing the function itself. Django uses them everywhere (`@login_required`, `@cache_page`, `@csrf_exempt`).

```python
import functools, time

def timer(func):
    @functools.wraps(func)    # preserves the wrapped function's metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)

slow_function()  # slow_function took 1.0002s
```

Decorators with arguments (decorator factories):
```python
def retry(max_attempts=3, delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=5, delay=0.5)
def flaky_api_call():
    ...
```

### Generators — Lazy Sequences

A generator produces values one at a time — perfect for large datasets or infinite sequences:

```python
def fibonacci():
    a, b = 0, 1
    while True:          # infinite, but lazy!
        yield a
        a, b = b, a + b

fib = fibonacci()
first_ten = [next(fib) for _ in range(10)]   # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# Generator expression — like list comp, but produces one item at a time
# This sums a million squares without ever building a million-item list:
total = sum(x**2 for x in range(1_000_000))
```

**Real-world use — streaming database results:**
```python
def stream_users():
    """Process users in chunks — never loads all into memory."""
    offset = 0
    chunk_size = 1000
    while True:
        chunk = User.objects.all()[offset:offset + chunk_size]
        if not chunk:
            break
        yield from chunk
        offset += chunk_size

for user in stream_users():
    process(user)  # only 1000 users in memory at a time
```

### itertools — The Generator Toolkit

```python
import itertools

# chain — combine multiple iterables into one
list(itertools.chain([1,2], [3,4], [5]))     # [1, 2, 3, 4, 5]

# groupby — group consecutive elements (must be sorted first!)
data = sorted([{"city":"NYC","name":"Alice"},{"city":"NYC","name":"Bob"},
               {"city":"LA","name":"Carol"}], key=lambda x: x["city"])
for city, group in itertools.groupby(data, key=lambda x: x["city"]):
    print(city, [p["name"] for p in group])

# combinations and permutations
list(itertools.combinations("ABC", 2))    # [('A','B'), ('A','C'), ('B','C')]
list(itertools.permutations("AB", 2))     # [('A','B'), ('B','A')]

# product — cartesian product (like nested for loops)
list(itertools.product("AB", [1,2]))      # [('A',1), ('A',2), ('B',1), ('B',2)]

# pairwise — consecutive pairs (Python 3.10+)
list(itertools.pairwise([1,2,3,4]))       # [(1,2), (2,3), (3,4)]
```

### functools — Higher-Order Functions

```python
import functools

# lru_cache — memoize expensive function calls
@functools.lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

fib(100)  # instant — each subproblem computed once

# partial — freeze some arguments of a function
def power(base, exponent): return base ** exponent
square = functools.partial(power, exponent=2)
cube   = functools.partial(power, exponent=3)
print(square(5))   # 25

# singledispatch — function overloading by type
@functools.singledispatch
def process(value):
    return f"Unknown: {type(value).__name__}"

@process.register(int)
def _(value): return f"Integer × 2 = {value * 2}"

@process.register(str)
def _(value): return f"String: {value.upper()}"

process(42)       # "Integer × 2 = 84"
process("hello")  # "String: HELLO"
```

---

## Chapter 4 — Advanced Python

> **File:** `04-advanced-python/04_advanced.py`

### Async/Await — Concurrent Without Threads

Python is single-threaded. `async/await` doesn't use multiple threads — it uses **cooperative multitasking**. When one coroutine is waiting for I/O, others run. Think of it as a chef who starts boiling water (I/O), then chops vegetables (another task) while waiting, rather than staring at the pot.

```python
import asyncio

# Sequential: waits 100ms, then waits 150ms = 250ms total
async def sequential():
    user   = await fetch_user(1)        # wait 100ms
    orders = await fetch_orders(1)      # THEN wait 150ms
    return {**user, "orders": orders}

# Concurrent: both start immediately = ~150ms total (longest wins)
async def concurrent():
    user, orders = await asyncio.gather(
        fetch_user(1),                  # starts immediately
        fetch_orders(1),                # also starts immediately
    )
    return {**user, "orders": orders}
```

**Key asyncio patterns:**
```python
# gather — run multiple coroutines, wait for ALL
results = await asyncio.gather(task1(), task2(), task3())

# gather with error handling
results = await asyncio.gather(task1(), task2(), return_exceptions=True)
# returns exceptions as values instead of raising

# wait_for — timeout
try:
    result = await asyncio.wait_for(slow_task(), timeout=5.0)
except asyncio.TimeoutError:
    result = None

# as_completed — process results as they finish (not in order)
for coro in asyncio.as_completed([task1(), task2(), task3()]):
    result = await coro
    print(f"Got: {result}")
```

### Type Hints — Advanced Usage

```python
from typing import TypeVar, Generic, Literal, TypedDict, Annotated, overload

# Generic classes
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None: self._items: list[T] = []
    def push(self, item: T) -> None: self._items.append(item)
    def pop(self) -> T: return self._items.pop()

stack: Stack[int] = Stack()  # fully typed

# TypedDict — typed dictionary
class UserDict(TypedDict):
    id: int
    name: str
    email: str

# Literal — restrict to specific values
Direction = Literal["north", "south", "east", "west"]
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]

# Annotated — add metadata (used by Pydantic, FastAPI, Django Ninja)
from typing import Annotated
PositiveInt = Annotated[int, "must be > 0"]
Email       = Annotated[str, "must contain @"]
```

---

## Chapter 5 — Django Core

> **File:** `05-django-core/05_django_core.py`

### Django's Request/Response Lifecycle

```
Browser → Nginx → Gunicorn → Django
                               ↓
                    SecurityMiddleware
                    SessionMiddleware
                    CommonMiddleware
                    CsrfViewMiddleware
                    AuthenticationMiddleware
                    YourCustomMiddleware
                               ↓
                         URL Router
                               ↓
                            View
                          ↙      ↘
                      Model    Template
                               ↓
                    (same middleware, reversed)
                               ↓
                           Response
```

Every request flows through this pipeline. Middleware is where you add cross-cutting concerns — logging, authentication checks, rate limiting, request IDs — without touching views.

### Settings Done Right

Never put settings in one file. Use a package:

```
myproject/settings/
    __init__.py       ← empty or imports base
    base.py           ← shared by all environments
    development.py    ← local dev (DEBUG=True, SQLite, etc.)
    production.py     ← production (HTTPS, PostgreSQL, S3, etc.)
    test.py           ← fast DB, no real email, in-memory cache
```

The golden rule: **secrets come from environment variables, never source code.**

```python
from decouple import config   # pip install python-decouple

SECRET_KEY = config("DJANGO_SECRET_KEY")   # required — will crash if missing
DEBUG       = config("DEBUG", default=False, cast=bool)
DATABASE_URL = config("DATABASE_URL", default="sqlite:///db.sqlite3")
```

### Custom Middleware

```python
class RequestIDMiddleware:
    """Attach a unique ID to every request for distributed tracing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id          # attach to request

        response = self.get_response(request)    # call the view

        response["X-Request-ID"] = request_id    # attach to response
        return response
```

---

## Chapter 6 — Django Models & ORM

> **File:** `06-django-models/06_models.py`

### Always Create a Custom User Model First

This is the #1 mistake new Django developers make. Django's built-in `User` model is difficult to extend after your first migration. Do this before you touch anything else:

```python
# users/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)    # make email unique
    bio   = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    USERNAME_FIELD = "email"                  # log in with email
    REQUIRED_FIELDS = ["username"]

# settings.py
AUTH_USER_MODEL = "users.User"
```

Set `AUTH_USER_MODEL` before running `python manage.py migrate`. Not after.

### Abstract Base Models — Your Mixins

```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # set on CREATE
    updated_at = models.DateTimeField(auto_now=True)       # set on every SAVE

    class Meta:
        abstract = True    # ← no table created, just a mixin

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    class Meta:
        abstract = True

# Compose them:
class Product(TimestampedModel, SoftDeleteModel):
    name = models.CharField(max_length=255)
    # inherits: created_at, updated_at, deleted_at, soft_delete()
```

### The QuerySet API — SQL Without SQL

```python
# Filter with lookups
Product.objects.filter(price__gte=100)          # WHERE price >= 100
Product.objects.filter(name__icontains="shirt") # WHERE UPPER(name) LIKE '%SHIRT%'
Product.objects.filter(tags__name="sale")       # JOIN to tags!
Product.objects.filter(metadata__color="red")   # JSON field lookup!

# Q objects for complex queries
from django.db.models import Q
Product.objects.filter(
    Q(price__lt=50) | Q(is_featured=True)        # OR
).exclude(
    Q(stock=0) & Q(is_active=False)              # AND NOT
)

# Aggregation
from django.db.models import Avg, Sum, Count
Product.objects.aggregate(avg_price=Avg("price"), total=Sum("stock"))

# Annotation — add a computed field to each object
Product.objects.annotate(
    review_count=Count("reviews"),
    avg_rating=Avg("reviews__rating"),
    revenue=F("price") * F("stock"),        # F() references DB column
)

# Avoid N+1: always select_related (FK) or prefetch_related (M2M/reverse FK)
Product.objects.select_related("category").prefetch_related("tags", "reviews")
```

### Custom Managers — Fat Model, Thin View

```python
class ProductQuerySet(models.QuerySet):
    def active(self):       return self.filter(is_active=True, deleted_at__isnull=True)
    def in_stock(self):     return self.filter(stock__gt=0)
    def featured(self):     return self.active().in_stock().filter(is_featured=True)
    def expensive(self, min_price=100): return self.filter(price__gte=min_price)

class ProductManager(models.Manager):
    def get_queryset(self): return ProductQuerySet(self.model, using=self._db)
    def active(self):       return self.get_queryset().active()
    def featured(self):     return self.get_queryset().featured()

class Product(TimestampedModel):
    objects = ProductManager()    # replace the default manager

# Now your queries are self-documenting:
featured = Product.objects.featured()[:10]
expensive_in_stock = Product.objects.active().expensive(200).in_stock()
```

---

## Chapter 7 — Views & URLs

> **File:** `07-django-views-urls/07_views_urls.py`

### Function-Based vs Class-Based Views

| | FBVs | CBVs |
|---|---|---|
| **When to use** | Simple, one-off, custom logic | Standard CRUD, reusable patterns |
| **Readability** | Explicit, easy to follow | Magic through inheritance |
| **Reusability** | Decorators | Mixins |
| **Testing** | Simple | Simple |

Both are good. Real projects use both.

```python
# FBV — explicit, no magic
@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            return redirect("products:detail", slug=product.slug)
    else:
        form = ProductForm()
    return render(request, "products/form.html", {"form": form})

# CBV — less code, more conventions
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"
    success_url = reverse_lazy("products:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user  # inject before save
        return super().form_valid(form)
```

### URL Patterns

```python
# products/urls.py
from django.urls import path
from . import views

app_name = "products"   # namespace — use as "products:detail" in reverse()

urlpatterns = [
    path("",                      views.ProductListView.as_view(),   name="list"),
    path("<slug:slug>/",          views.ProductDetailView.as_view(), name="detail"),
    path("new/",                  views.ProductCreateView.as_view(), name="create"),
    path("<slug:slug>/edit/",     views.ProductUpdateView.as_view(), name="update"),
    path("<slug:slug>/delete/",   views.ProductDeleteView.as_view(), name="delete"),
]

# Reverse a URL anywhere in your code (never hardcode URLs):
from django.urls import reverse
url = reverse("products:detail", kwargs={"slug": "my-product"})
# → "/products/my-product/"
```

---

## Chapter 8 — Django REST Framework

> **File:** `08-django-rest-framework/08_drf.py`

### Why DRF?

Django REST Framework is to Django what Django is to Python — it makes 80% of your work disappear. Serialization, validation, authentication, permissions, pagination, filtering, throttling, and API documentation — all handled, all configurable.

### Serializers — Your Input/Output Contract

Always use separate serializers for input and output. Your client's PUT/POST payload rarely looks like what you return in GET:

```python
# Input — what we accept
class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "price", "stock", "category", "description"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        product = super().create(validated_data)
        product.tags.set(tags)    # M2M must be set after save
        return product

# Output — what we return (richer, nested)
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags     = TagSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "in_stock", "category", "tags", "created_at"]
```

### ViewSets — Full CRUD in ~30 Lines

```python
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = ProductFilter
    search_fields      = ["name", "description"]
    ordering_fields    = ["name", "price", "created_at"]

    def get_queryset(self):
        return Product.objects.active().select_related("category").prefetch_related("tags")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductCreateSerializer
        return ProductDetailSerializer

    @action(detail=True, methods=["post"])
    def feature(self, request, pk=None):
        """POST /products/{id}/feature/ — custom action"""
        product = self.get_object()
        product.is_featured = True
        product.save()
        return Response({"status": "Product featured"})
```

Wire it up with a router — zero URL configuration:
```python
router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
# Generates: GET/POST /products/, GET/PUT/PATCH/DELETE /products/{id}/,
#            POST /products/{id}/feature/
```

---

## Chapter 9 — Auth & Security

> **File:** `09-django-auth-security/09_auth_security.py`

### JWT Authentication Flow

```
1. POST /api/auth/login/
   { "email": "alice@example.com", "password": "..." }

2. Server validates credentials → generates:
   access_token  (15 min lifespan — short by design)
   refresh_token (7 day lifespan)

3. Client stores tokens (NOT in localStorage — use httpOnly cookies)

4. Every API request:
   Authorization: Bearer <access_token>

5. When access token expires (401):
   POST /api/auth/refresh/ { "refresh": "<refresh_token>" }
   → new access_token issued

6. On logout:
   POST /api/auth/logout/ { "refresh": "<refresh_token>" }
   → refresh token blacklisted in DB
```

### Never Do These Things

```python
# ❌ Hardcoded secret
SECRET_KEY = "my-secret-key"

# ❌ SQL injection via string formatting
Product.objects.raw(f"SELECT * FROM products WHERE name = '{name}'")

# ❌ Trusting user-supplied IDs without ownership check
product = Product.objects.get(id=request.data["id"])

# ❌ Revealing which field is wrong on login
if not User.objects.filter(email=email).exists():
    return Response({"error": "Email not found"})  # user enumeration!

# ✅ Same message for wrong email AND wrong password
return Response({"error": "Invalid credentials."})  # never reveals which
```

### `python manage.py check --deploy`

Run this before going live. Django's built-in deployment checker catches the most common security misconfigurations and will tell you exactly what to fix.

---

## Chapter 10 — Testing

> **File:** `10-testing/10_testing.py`

### The Golden Rule: Test Behaviour, Not Implementation

Don't test that a method was called — test that the outcome is correct. Tests that mirror implementation are brittle; they break every refactor.

```python
# ❌ Tests implementation (brittle)
def test_creates_user():
    with patch("users.services.User.objects.create") as mock_create:
        register_user("alice@example.com", "password")
        mock_create.assert_called_once()   # breaks on any refactor

# ✅ Tests behaviour (robust)
@pytest.mark.django_db
def test_creates_user():
    register_user("alice@example.com", "password")
    assert User.objects.filter(email="alice@example.com").exists()  # what matters
```

### Factory Boy — Test Data Without Pain

```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email      = factory.LazyAttribute(lambda _: fake.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    is_active  = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "testpassword123!")
        if create: obj.save()

# Usage:
user    = UserFactory()                           # creates one
admin   = UserFactory(is_staff=True)              # with override
users   = UserFactory.create_batch(10)            # creates ten
product = ProductFactory(price=99.99, category__name="Electronics")  # nested override
```

### Slice Tests Appropriately

```python
# @WebMvcTest equivalent: only load web layer
@pytest.mark.django_db
class TestProductAPI:
    def test_list_returns_200(self, api_client):
        ProductFactory.create_batch(3)
        response = api_client.get("/api/v1/products/")
        assert response.status_code == 200
        assert response.data["count"] == 3

    def test_create_requires_auth(self, api_client):
        response = api_client.post("/api/v1/products/", {"name": "Test"})
        assert response.status_code == 401

    @patch("views.send_welcome_email.delay")   # mock the Celery task
    def test_register_fires_welcome_email(self, mock_task, api_client):
        api_client.post("/api/v1/auth/register/", {
            "email": "alice@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        })
        mock_task.assert_called_once()
```

---

## Chapter 11 — AI/ML Fundamentals

> **File:** `11-ai-ml-fundamentals/11_ai_ml.py`

### Why Python Dominates AI/ML

1. **NumPy** — fast array math (operations run in C, not Python)
2. **Pandas** — data manipulation (think SQL in Python)
3. **scikit-learn** — classical ML with a consistent API
4. **PyTorch / TensorFlow** — deep learning
5. **HuggingFace Transformers** — pretrained models for everything

The ecosystem is so mature that Python isn't just popular for AI — it's effectively the only language for it.

### NumPy — Vectorization is Everything

```python
import numpy as np

# The rule: if you're looping over a NumPy array, you're doing it wrong
a = np.array([1.0, 2.0, 3.0, 4.0])

# Vectorized — runs in compiled C, extremely fast:
result = a ** 2 + 2 * a + 1   # [4, 9, 16, 25]

# Equivalent loop — 100x slower for large arrays:
result = [x**2 + 2*x + 1 for x in a]

# Boolean indexing — filter without loops:
data = np.array([15, 8, 22, 3, 45, 11])
data[data > 15]             # array([22, 45])
data[data % 2 == 0]         # array([8, 22])
data[(data > 5) & (data < 20)]  # array([15, 8, 11])
```

### The Standard ML Workflow

Every ML project follows the same structure. Master this template:

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# 1. Load data
X, y = load_your_data()

# 2. Split FIRST — never touch test data during development!
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 3. Build pipeline — preprocessing + model in one object
pipeline = Pipeline([
    ("scaler",     StandardScaler()),
    ("classifier", RandomForestClassifier(n_estimators=100, random_state=42)),
])

# 4. Cross-validate on training data
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
print(f"CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# 5. Train on ALL training data
pipeline.fit(X_train, y_train)

# 6. Evaluate on test set — only once, at the very end
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))
```

**Why pipelines?** They guarantee that preprocessing is fit on training data only, and the same transformation is applied to test data — no data leakage.

---

## Chapter 12 — NLP, LLMs & RAG

> **File:** `12-ai-nlp-llms/12_ai_nlp_llms.py`

### Embeddings — The Math Behind Semantic Search

An embedding is a list of numbers (a vector) that captures the *meaning* of text. Similar meanings produce similar vectors. This is the foundation of modern AI search, recommendations, and RAG.

```python
"cat"  → [0.23, -0.45, 0.78, ...]   # 1536 numbers
"dog"  → [0.21, -0.43, 0.75, ...]   # similar! (semantically related)
"SQL"  → [0.89,  0.12, -0.33, ...]  # very different
```

Cosine similarity between "cat" and "dog" ≈ 0.85 (high — related concepts)
Cosine similarity between "cat" and "SQL" ≈ 0.12 (low — unrelated)

### RAG — Make LLMs Know Your Data

LLMs have a knowledge cutoff. Your data isn't in them. RAG solves this:

```
YOUR DOCUMENTS → embed → vector database

USER QUERY → embed → find similar chunks → inject into prompt → LLM answers
```

```python
# The three steps:

# 1. INDEX: embed all your documents (done once, or as docs are added)
for doc in documents:
    embedding = openai.embeddings.create(input=doc.content, model="text-embedding-3-small")
    vector_db.upsert(id=doc.id, vector=embedding, metadata={"text": doc.content})

# 2. RETRIEVE: find relevant chunks for a user query
query_embedding = openai.embeddings.create(input=user_query, model="text-embedding-3-small")
similar_chunks = vector_db.query(vector=query_embedding, top_k=4)

# 3. GENERATE: answer using the retrieved context
context = "\n\n".join([chunk["text"] for chunk in similar_chunks])
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"Answer using only this context:\n\n{context}"},
        {"role": "user",   "content": user_query},
    ]
)
```

### Prompt Engineering Patterns That Actually Work

**Chain of Thought** — tell the LLM to show its work:
```
"Solve step by step. Show your reasoning before the final answer."
```
This dramatically improves accuracy on math, logic, and multi-step problems.

**Few-Shot** — show examples:
```
Input: "The movie was amazing!"  Output: POSITIVE
Input: "I hated every minute."   Output: NEGATIVE
Input: "It was okay."            Output: ???
```

**Structured Output** — specify exactly what format you want:
```
Return ONLY a JSON object with keys: name, age, email.
Do not include any explanation or markdown.
```

**Role Prompting** — assign a persona:
```
"You are a senior Python engineer reviewing code for a high-traffic production API."
```

---

## Chapter 13 — Real-World Patterns

> **File:** `13-real-world-patterns/13_patterns.py`

### The Service Layer — Where Business Logic Lives

Keep views thin. Keep models focused on data. Put complex business logic in a **service layer**:

```
View:    validates HTTP request → calls service → returns response
Service: business logic, orchestration, side effects
Model:   data structure, simple queries, constraints
```

```python
class UserService:
    def register_user(self, email: str, password: str, name: str) -> User:
        email = email.lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValueError(f"Email already registered: {email}")

        user = User.objects.create_user(email=email, password=password, name=name)

        # Side effects — async via Celery, not blocking the response
        send_welcome_email.delay(user.pk)
        track_registration.delay(user.pk)
        return user
```

### Celery — Move Slow Work Out of Requests

Users shouldn't wait for your app to send an email, generate a PDF, or call an external API. Move it to a background task:

```python
# tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,))
def send_welcome_email(self, user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    send_mail(
        subject="Welcome!",
        message=f"Hi {user.get_full_name()}",
        recipient_list=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )

# In your view or service — fires and forgets:
send_welcome_email.delay(user.pk)   # returns immediately, runs in background
```

### Caching — Don't Compute the Same Thing Twice

```python
from django.core.cache import cache

def get_featured_products():
    cache_key = "featured_products"
    result = cache.get(cache_key)
    if result is None:
        result = list(Product.objects.featured()[:10])
        cache.set(cache_key, result, timeout=300)  # cache 5 minutes
    return result

# Django's cache decorators for views:
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)   # cache this view for 15 minutes
def product_list(request):
    ...
```

---

## Chapter 14 — Deployment

> **File:** `14-deployment/14_deployment.py`

### Docker in One Diagram

```
Dockerfile    →  docker build  →  Image (snapshot of your app)
docker-compose →  docker up    →  Containers (running instances)
```

Your `docker-compose.yml` defines your entire local dev environment: app server, database, Redis, Celery worker — all wired together, all reproducible.

### The CI/CD Pipeline

```
git push main
     ↓
GitHub Actions triggers:
  1. Lint (black, isort, flake8)
  2. Type check (mypy)
  3. Tests with coverage (must be ≥ 80%)
  4. Security scan (pip-audit, safety, django check --deploy)
  5. Build Docker image
  6. Push to container registry
  7. Deploy to production (with manual approval gate)
```

If any step fails, the pipeline stops. Your main branch is always deployable.

### Production Checklist

Before you go live, run: `python manage.py check --deploy`

Then verify manually:
- `DEBUG = False`
- `SECRET_KEY` from environment variable (not hardcoded)
- `ALLOWED_HOSTS` configured
- HTTPS enforced (`SECURE_SSL_REDIRECT = True`)
- Database is PostgreSQL (not SQLite)
- Static files configured (WhiteNoise or S3)
- Media files on S3/cloud storage (not local disk)
- Celery workers running
- Error tracking (Sentry) configured
- Log shipping to central location
- Health check endpoint responds

---

## Quick Reference

### Python One-Liners Worth Memorizing

```python
# Flatten a list of lists
flat = [x for row in nested for x in row]
# or: flat = list(itertools.chain.from_iterable(nested))

# Dict from two lists
d = dict(zip(keys, values))
# or: d = {k: v for k, v in zip(keys, values)}

# Count occurrences
from collections import Counter
counts = Counter(["a", "b", "a", "c", "b", "a"])   # Counter({'a': 3, 'b': 2, 'c': 1})

# Group by a key
from itertools import groupby
data.sort(key=lambda x: x["city"])
grouped = {k: list(v) for k, v in groupby(data, key=lambda x: x["city"])}

# Get first match or default
first = next((x for x in items if x.active), None)

# Unique while preserving order
seen = set(); unique = [x for x in items if not (x in seen or seen.add(x))]

# Merge dicts (Python 3.9+)
merged = base | overrides   # overrides win

# Swap variables
a, b = b, a
```

### Django QuerySet Quick Reference

```python
# Fetch
.all()                      # all objects (lazy!)
.filter(field=value)        # WHERE
.exclude(field=value)       # WHERE NOT
.get(field=value)           # exactly one — raises if 0 or 2+
.first() / .last()          # or None
.exists()                   # SELECT EXISTS (fastest count check)
.count()                    # SELECT COUNT

# Lookups
.filter(price__gte=100)     # >=
.filter(name__icontains="x")# ILIKE '%x%'
.filter(tags__name="sale")  # JOIN
.filter(meta__key="value")  # JSON field

# Select
.values("id", "name")       # dicts
.values_list("id", flat=True) # flat list
.only("id", "name")         # partial objects
.defer("large_field")       # exclude large field

# Performance
.select_related("category") # JOIN (ForeignKey)
.prefetch_related("tags")   # separate query (M2M)

# Aggregate
.aggregate(avg=Avg("price"), total=Sum("stock"))
.annotate(count=Count("reviews"))

# Update
.update(is_active=False)    # bulk UPDATE
.update(stock=F("stock")-1) # atomic! use F() always for arithmetic
```

### DRF Status Codes Reference

```python
from rest_framework import status

HTTP_200_OK                  # GET success
HTTP_201_CREATED             # POST success (include Location header)
HTTP_204_NO_CONTENT          # DELETE success (no body)
HTTP_400_BAD_REQUEST         # validation error
HTTP_401_UNAUTHORIZED        # not authenticated
HTTP_403_FORBIDDEN           # authenticated but not authorized
HTTP_404_NOT_FOUND           # resource doesn't exist
HTTP_409_CONFLICT            # duplicate resource
HTTP_422_UNPROCESSABLE_ENTITY # semantic validation failure
HTTP_429_TOO_MANY_REQUESTS   # rate limited
HTTP_503_SERVICE_UNAVAILABLE  # external dependency down
```

### OpenAI API Quick Reference

```python
from openai import OpenAI
client = OpenAI()   # reads OPENAI_API_KEY from environment

# Chat completion
response = client.chat.completions.create(
    model="gpt-4o-mini",     # or "gpt-4o" for smarter
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "Your question here"},
    ],
    temperature=0.7,          # 0=deterministic, 2=wild
    max_tokens=1000,
    response_format={"type": "json_object"},  # structured output
)
text = response.choices[0].message.content
tokens = response.usage.total_tokens

# Embeddings
response = client.embeddings.create(
    input="text to embed",
    model="text-embedding-3-small",   # 1536 dims, fast + cheap
    # model="text-embedding-3-large", # 3072 dims, more accurate
)
vector = response.data[0].embedding   # list of floats

# Streaming
for chunk in client.chat.completions.create(..., stream=True):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

*Python is a language that grows with you. Start with Chapter 1 and don't stop. The distance between "Hello, World!" and building an AI-powered production API is smaller than you think — and every step of the journey is genuinely fun.*

*Happy coding. 🐍*
