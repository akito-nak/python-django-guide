"""
============================================================
02 - OBJECT-ORIENTED PROGRAMMING IN PYTHON
============================================================
Python's OOP is more flexible than Java's — everything is an
object, classes are objects, functions are objects. This
flexibility is powerful but requires discipline to use well.

Key Python-specific features: dunder methods, properties,
descriptors, dataclasses, and Protocols (structural typing).
============================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
import functools


# ─────────────────────────────────────────────────────────────
# BASIC CLASS ANATOMY
# ─────────────────────────────────────────────────────────────

class BankAccount:
    """
    A bank account with balance protection.
    Demonstrates encapsulation, properties, and dunder methods.
    """

    # Class variable — shared across ALL instances
    interest_rate: float = 0.03
    _total_accounts: int = 0     # "private" by convention (single underscore)

    def __init__(self, owner: str, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self._owner = owner                  # "protected" — use getter/setter
        self.__balance = initial_balance     # "private" — name mangled to _BankAccount__balance
        self._transactions: list[float] = []
        BankAccount._total_accounts += 1

    # ── Properties — controlled access to private data ────────
    @property
    def balance(self) -> float:
        """Read-only balance — no setter means it can't be set directly."""
        return self.__balance

    @property
    def owner(self) -> str:
        return self._owner

    @owner.setter
    def owner(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Owner name cannot be empty")
        self._owner = value.strip()

    # ── Instance methods ──────────────────────────────────────
    def deposit(self, amount: float) -> BankAccount:
        """Deposit money. Returns self for method chaining."""
        if amount <= 0:
            raise ValueError(f"Deposit amount must be positive, got {amount}")
        self.__balance += amount
        self._transactions.append(amount)
        return self  # enables: account.deposit(100).deposit(50)

    def withdraw(self, amount: float) -> BankAccount:
        """Withdraw money."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.__balance:
            raise ValueError(f"Insufficient funds: balance is {self.__balance:.2f}")
        self.__balance -= amount
        self._transactions.append(-amount)
        return self

    def get_statement(self) -> str:
        lines = [f"Account: {self._owner}", f"Balance: ${self.__balance:.2f}", "Transactions:"]
        for i, t in enumerate(self._transactions, 1):
            sign = "+" if t > 0 else ""
            lines.append(f"  {i:3}. {sign}${t:.2f}")
        return "\n".join(lines)

    # ── Class methods — work on the class, not instances ──────
    @classmethod
    def total_accounts(cls) -> int:
        return cls._total_accounts

    @classmethod
    def from_dict(cls, data: dict) -> BankAccount:
        """Alternative constructor — factory pattern."""
        return cls(data["owner"], data.get("balance", 0.0))

    # ── Static methods — utility, no class or instance needed ──
    @staticmethod
    def validate_routing_number(routing: str) -> bool:
        """Validates a US routing number (9 digits)."""
        return routing.isdigit() and len(routing) == 9

    # ── Dunder (magic) methods — make your class feel Pythonic ─
    def __repr__(self) -> str:
        """Unambiguous string for developers (used in REPL, logs)."""
        return f"BankAccount(owner={self._owner!r}, balance={self.__balance:.2f})"

    def __str__(self) -> str:
        """Human-readable string (used in print())."""
        return f"{self._owner}'s account: ${self.__balance:.2f}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BankAccount):
            return NotImplemented
        return self._owner == other._owner and self.__balance == other.__balance

    def __lt__(self, other: BankAccount) -> bool:
        return self.__balance < other.__balance

    def __add__(self, other: BankAccount) -> BankAccount:
        """Merge two accounts: account1 + account2."""
        merged = BankAccount(f"{self._owner} & {other._owner}")
        merged.__balance = self.__balance + other.__balance  # type: ignore
        return merged

    def __len__(self) -> int:
        return len(self._transactions)

    def __bool__(self) -> bool:
        return self.__balance > 0

    def __contains__(self, amount: float) -> bool:
        """Check if a transaction amount exists: 100.0 in account."""
        return amount in self._transactions

    def __iter__(self):
        return iter(self._transactions)

    def __getitem__(self, index: int) -> float:
        return self._transactions[index]


# ─────────────────────────────────────────────────────────────
# INHERITANCE
# ─────────────────────────────────────────────────────────────

class SavingsAccount(BankAccount):
    def __init__(self, owner: str, initial_balance: float = 0.0,
                 minimum_balance: float = 100.0) -> None:
        super().__init__(owner, initial_balance)
        self.minimum_balance = minimum_balance

    def withdraw(self, amount: float) -> SavingsAccount:
        if self.balance - amount < self.minimum_balance:
            raise ValueError(
                f"Cannot withdraw: would go below minimum balance of ${self.minimum_balance:.2f}"
            )
        return super().withdraw(amount)  # type: ignore

    def apply_interest(self) -> SavingsAccount:
        interest = self.balance * self.interest_rate
        self.deposit(interest)
        print(f"Interest applied: +${interest:.2f}")
        return self

    def __repr__(self) -> str:
        return f"SavingsAccount(owner={self.owner!r}, balance={self.balance:.2f})"


# ─────────────────────────────────────────────────────────────
# ABSTRACT BASE CLASSES — enforce a contract
# ─────────────────────────────────────────────────────────────

class Shape(ABC):
    """Abstract base class — cannot be instantiated directly."""

    def __init__(self, color: str = "black") -> None:
        self.color = color

    @abstractmethod
    def area(self) -> float:
        """Every Shape must implement area()."""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        """Every Shape must implement perimeter()."""
        ...

    def describe(self) -> str:
        """Concrete method — available to all subclasses."""
        return (f"{self.color.capitalize()} {self.__class__.__name__}: "
                f"area={self.area():.2f}, perimeter={self.perimeter():.2f}")


class Circle(Shape):
    import math  # local import is fine here

    def __init__(self, radius: float, color: str = "black") -> None:
        super().__init__(color)
        self.radius = radius

    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius


class Rectangle(Shape):
    def __init__(self, width: float, height: float, color: str = "black") -> None:
        super().__init__(color)
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


# ─────────────────────────────────────────────────────────────
# DATACLASSES — cut the boilerplate, keep the clarity
# ─────────────────────────────────────────────────────────────
# @dataclass auto-generates __init__, __repr__, __eq__, and more.
# Use for data-holding classes (like Java Records or structs).

@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)


@dataclass
class User:
    name: str
    email: str
    age: int
    tags: list[str] = field(default_factory=list)   # ⚠️ mutable defaults MUST use field()
    _id: int = field(default=0, repr=False)          # excluded from __repr__

    def __post_init__(self) -> None:
        """Called after __init__ — for validation."""
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
        if self.age < 0:
            raise ValueError(f"Age cannot be negative: {self.age}")
        self.email = self.email.lower()


@dataclass(frozen=True)    # frozen=True → immutable (like a tuple with names)
class Coordinate:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")

    @classmethod
    def from_string(cls, s: str) -> Coordinate:
        """Parse '40.7128,-74.0060' into a Coordinate."""
        lat, lon = map(float, s.split(","))
        return cls(lat, lon)


@dataclass(order=True)     # order=True → enables <, >, <=, >= based on fields
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


# ─────────────────────────────────────────────────────────────
# PROTOCOLS — structural subtyping ("duck typing with types")
# ─────────────────────────────────────────────────────────────
# A Protocol says: "I don't care what TYPE you are —
# I care that you have these METHODS."
# No inheritance required — any class with the right methods qualifies.

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...
    def resize(self, factor: float) -> None: ...


@runtime_checkable
class Saveable(Protocol):
    def save(self) -> bytes: ...
    def load(self, data: bytes) -> None: ...


# These classes DON'T inherit from Drawable — they just implement its methods
class SVGCircle:
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def draw(self) -> str:
        return f'<circle r="{self.radius}"/>'

    def resize(self, factor: float) -> None:
        self.radius *= factor


class PNGImage:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def draw(self) -> str:
        return f"[PNG {self.width}x{self.height}]"

    def resize(self, factor: float) -> None:
        self.width = int(self.width * factor)
        self.height = int(self.height * factor)


def render(drawable: Drawable) -> str:
    """Works with ANY object that has draw() and resize() — no inheritance!"""
    return drawable.draw()


# isinstance works with @runtime_checkable protocols
circle = SVGCircle(5.0)
print(isinstance(circle, Drawable))   # True — it has draw() and resize()


# ─────────────────────────────────────────────────────────────
# MIXINS — composable behaviour without deep inheritance
# ─────────────────────────────────────────────────────────────

class TimestampMixin:
    """Add created_at/updated_at to any model."""
    from datetime import datetime

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        from datetime import datetime
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def touch(self) -> None:
        from datetime import datetime
        self.updated_at = datetime.now()


class SerializeMixin:
    """Add JSON serialization to any class."""
    import json

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), default=str)


class AuditMixin:
    """Track who created/modified a record."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.created_by: str | None = None
        self.modified_by: str | None = None


# Combine mixins — Python uses Method Resolution Order (MRO) to resolve calls
class Article(TimestampMixin, SerializeMixin, AuditMixin):
    def __init__(self, title: str, content: str) -> None:
        super().__init__()  # MRO ensures all mixins' __init__ are called
        self.title = title
        self.content = content


# ─────────────────────────────────────────────────────────────
# CONTEXT MANAGERS — the `with` statement
# ─────────────────────────────────────────────────────────────

class DatabaseConnection:
    """Resource management with guaranteed cleanup."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.connection = None

    def __enter__(self) -> DatabaseConnection:
        """Called at the start of `with` block."""
        print(f"Opening connection to {self.url}")
        self.connection = f"<connected:{self.url}>"  # simulate connection
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Called at the END of `with` block — even if exception occurred!"""
        print(f"Closing connection to {self.url}")
        self.connection = None
        # Return True to suppress exceptions, False (or None) to propagate
        return False

    def query(self, sql: str) -> list:
        if not self.connection:
            raise RuntimeError("Not connected")
        print(f"Executing: {sql}")
        return []


# Usage — connection is ALWAYS closed, even if an exception occurs
with DatabaseConnection("postgresql://localhost/mydb") as db:
    results = db.query("SELECT * FROM users")


# Simpler: use contextlib
from contextlib import contextmanager

@contextmanager
def timer(label: str = ""):
    import time
    start = time.perf_counter()
    try:
        yield  # everything in the `with` block runs here
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.4f}s")


with timer("My operation"):
    total = sum(x**2 for x in range(100_000))


if __name__ == "__main__":
    # BankAccount demo
    account = BankAccount("Alice", 1000)
    account.deposit(500).deposit(250).withdraw(100)
    print(account)
    print(repr(account))
    print(f"Transactions: {len(account)}")

    # Dataclass demo
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    print(f"Distance: {p1.distance_to(p2)}")

    user = User("Akito", "akito@example.com", 35, tags=["python", "django"])
    print(user)

    # Shape demo
    shapes: list[Shape] = [Circle(5, "red"), Rectangle(4, 6, "blue")]
    for shape in shapes:
        print(shape.describe())
