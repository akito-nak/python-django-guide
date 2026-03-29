"""
============================================================
10 - TESTING IN DJANGO
============================================================
"Untested code is broken code you haven't found yet."

Django has a first-class testing story. Combine Django's test
client, pytest-django, factory_boy for fixtures, and coverage
for measurement — and you have a testing setup that'll catch
regressions before your users do.

Install:
  pip install pytest pytest-django factory_boy pytest-cov faker
============================================================
"""

# ─────────────────────────────────────────────────────────────
# PYTEST CONFIGURATION
# ─────────────────────────────────────────────────────────────

PYTEST_INI = """
# pytest.ini (or pyproject.toml [tool.pytest.ini_options])
[pytest]
DJANGO_SETTINGS_MODULE = myproject.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --reuse-db           # reuse test DB between runs (faster)
    --no-header
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80  # fail if coverage < 80%
markers =
    slow: mark tests as slow (skipped by default, use -m slow to run)
    integration: mark as integration tests
"""

SETTINGS_TEST = """
# settings/test.py
from .base import *  # noqa

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_myapp",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        # Or use SQLite for speed (loses some PostgreSQL-specific features)
        # "ENGINE": "django.db.backends.sqlite3",
        # "NAME": ":memory:",
    }
}

# Use in-memory cache in tests — no Redis needed
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Faster password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use console email backend — emails appear in output, not actually sent
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery tasks run synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
"""


# ─────────────────────────────────────────────────────────────
# FACTORIES — create test data without repetition
# ─────────────────────────────────────────────────────────────

FACTORY_EXAMPLES = """
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = "users.User"
        django_get_or_create = ("email",)  # idempotent

    email      = factory.LazyAttribute(lambda _: fake.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name  = factory.LazyAttribute(lambda _: fake.last_name())
    is_active  = True
    is_verified = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        # Set a usable password after creation
        password = extracted or "testpassword123!"
        obj.set_password(password)
        if create:
            obj.save()


class AdminUserFactory(UserFactory):
    is_staff    = True
    is_superuser = True


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = "products.Category"

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "products.Product"

    name     = factory.LazyAttribute(lambda _: fake.word().capitalize())
    slug     = factory.LazyAttribute(lambda obj: obj.name.lower())
    price    = factory.LazyAttribute(lambda _: round(fake.random.uniform(1, 1000), 2))
    stock    = factory.LazyAttribute(lambda _: fake.random_int(0, 100))
    category = factory.SubFactory(CategoryFactory)
    is_active = True

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                obj.tags.add(tag)


# Usage in tests:
# user = UserFactory()                    # create and save
# user = UserFactory.build()              # build but DON'T save (faster)
# users = UserFactory.create_batch(5)     # create 5 users
# admin = AdminUserFactory()
# product = ProductFactory(price=99.99, category__name="Electronics")
#                                          # ↑ overriding nested factory
"""


# ─────────────────────────────────────────────────────────────
# MODEL TESTS
# ─────────────────────────────────────────────────────────────

MODEL_TESTS = """
# tests/test_models.py
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from tests.factories import UserFactory, ProductFactory, CategoryFactory


@pytest.mark.django_db  # gives test access to the database
class TestProduct:

    def test_create_product(self):
        product = ProductFactory()
        assert product.pk is not None
        assert product.is_active is True

    def test_in_stock_property(self):
        in_stock = ProductFactory(stock=10)
        out_of_stock = ProductFactory(stock=0)

        assert in_stock.in_stock is True
        assert out_of_stock.in_stock is False

    def test_apply_discount(self):
        product = ProductFactory(price=Decimal("100.00"))
        product.apply_discount(10)  # 10%
        product.refresh_from_db()   # reload from DB
        assert product.price == Decimal("90.00")

    def test_apply_discount_invalid(self):
        product = ProductFactory()
        with pytest.raises(ValueError, match="between 0 and 100"):
            product.apply_discount(150)

    def test_slug_uniqueness(self):
        ProductFactory(slug="my-product")
        with pytest.raises(Exception):  # IntegrityError
            ProductFactory(slug="my-product")

    @pytest.mark.parametrize("price,expected", [
        (Decimal("100.00"), Decimal("90.00")),  # 10% off 100 = 90
        (Decimal("50.00"),  Decimal("45.00")),  # 10% off 50 = 45
        (Decimal("0.99"),   Decimal("0.89")),   # 10% off 0.99 ≈ 0.89
    ])
    def test_apply_discount_parametrized(self, price, expected):
        product = ProductFactory(price=price)
        product.apply_discount(10)
        product.refresh_from_db()
        assert abs(product.price - expected) < Decimal("0.01")


@pytest.mark.django_db
class TestUser:

    def test_create_user(self):
        user = UserFactory()
        assert user.email is not None
        assert "@" in user.email
        assert user.check_password("testpassword123!")  # factory sets this

    def test_full_name(self):
        user = UserFactory(first_name="Alice", last_name="Smith")
        assert user.get_full_name() == "Alice Smith"

    def test_email_is_lowercase(self):
        user = UserFactory(email="ALICE@EXAMPLE.COM")
        assert user.email == "alice@example.com"
"""


# ─────────────────────────────────────────────────────────────
# API / VIEW TESTS
# ─────────────────────────────────────────────────────────────

VIEW_TESTS = """
# tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from tests.factories import UserFactory, ProductFactory, CategoryFactory


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def admin_client(api_client):
    admin = UserFactory(is_staff=True)
    api_client.force_authenticate(user=admin)
    return api_client, admin


@pytest.mark.django_db
class TestProductEndpoints:

    def test_list_products_unauthenticated(self, api_client):
        ProductFactory.create_batch(3)
        response = api_client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_list_products_pagination(self, api_client):
        ProductFactory.create_batch(25)
        response = api_client.get("/api/v1/products/?page=1&page_size=10")
        assert response.status_code == 200
        assert len(response.data["results"]) == 10
        assert response.data["count"] == 25

    def test_filter_products_by_price(self, api_client):
        ProductFactory(price=50)
        ProductFactory(price=100)
        ProductFactory(price=200)

        response = api_client.get("/api/v1/products/?min_price=75&max_price=150")
        assert response.status_code == 200
        assert response.data["count"] == 1  # only the 100-priced one

    def test_get_product_detail(self, api_client):
        product = ProductFactory()
        response = api_client.get(f"/api/v1/products/{product.pk}/")
        assert response.status_code == 200
        assert response.data["name"] == product.name
        assert response.data["price"] == str(product.price)

    def test_create_product_unauthenticated(self, api_client):
        data = {"name": "Test", "price": "29.99", "stock": 10}
        response = api_client.post("/api/v1/products/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_as_admin(self, admin_client):
        api_client, admin = admin_client
        category = CategoryFactory()
        data = {
            "name": "New Product",
            "price": "99.99",
            "stock": 50,
            "category": category.pk,
        }
        response = api_client.post("/api/v1/products/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Product"

    def test_create_product_validation_errors(self, admin_client):
        api_client, _ = admin_client
        data = {"name": "", "price": "-10", "stock": -1}
        response = api_client.post("/api/v1/products/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check field errors are present
        assert "name" in response.data.get("details", {})
        assert "price" in response.data.get("details", {})

    def test_delete_product_as_admin(self, admin_client):
        api_client, _ = admin_client
        product = ProductFactory()
        response = api_client.delete(f"/api/v1/products/{product.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Soft deleted — still in DB
        product.refresh_from_db()
        assert product.is_deleted is True

    def test_search_products(self, api_client):
        ProductFactory(name="Blue Shirt")
        ProductFactory(name="Red Shirt")
        ProductFactory(name="Green Pants")

        response = api_client.get("/api/v1/products/?search=shirt")
        assert response.status_code == 200
        assert response.data["count"] == 2


@pytest.mark.django_db
class TestAuthEndpoints:

    def test_register(self, api_client):
        data = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Alice",
            "last_name": "Smith",
        }
        response = api_client.post("/api/v1/auth/register/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_duplicate_email(self, api_client):
        UserFactory(email="existing@example.com")
        data = {
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Bob",
            "last_name": "Jones",
        }
        response = api_client.post("/api/v1/auth/register/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login(self, api_client):
        user = UserFactory()
        response = api_client.post("/api/v1/auth/login/", {
            "email": user.email,
            "password": "testpassword123!"
        })
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, api_client):
        user = UserFactory()
        response = api_client.post("/api/v1/auth/login/", {
            "email": user.email,
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
"""


# ─────────────────────────────────────────────────────────────
# MOCKING — isolate external dependencies
# ─────────────────────────────────────────────────────────────

MOCKING_EXAMPLES = """
# tests/test_ai_views.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from rest_framework.test import APIClient
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAIEndpoints:

    @patch("views.OpenAI")  # mock the OpenAI client
    def test_document_qa(self, mock_openai_class, authenticated_client):
        api_client, user = authenticated_client

        # Setup the mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is the AI answer."
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create.return_value = mock_response

        # Call the endpoint
        response = api_client.post("/api/v1/ai/qa/", {
            "query": "What is Django?",
            "document_ids": [1, 2],
        }, format="json")

        assert response.status_code == 200
        assert response.data["answer"] == "This is the AI answer."
        assert response.data["tokens_used"] == 150

        # Verify the mock was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"

    @patch("views.OpenAI")
    def test_document_qa_openai_error(self, mock_openai_class, authenticated_client):
        api_client, user = authenticated_client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        response = api_client.post("/api/v1/ai/qa/", {
            "query": "Test",
            "document_ids": [1],
        }, format="json")

        assert response.status_code == 503  # Service Unavailable
        assert "temporarily unavailable" in response.data["error"]

    @patch("django.core.mail.send_mail")
    def test_registration_sends_email(self, mock_send_mail, api_client):
        response = api_client.post("/api/v1/auth/register/", {
            "email": "alice@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "Alice",
            "last_name": "Smith",
        })
        assert response.status_code == 201
        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args[1]
        assert call_kwargs["recipient_list"] == ["alice@example.com"]
"""


# ─────────────────────────────────────────────────────────────
# FIXTURES — shared test setup
# ─────────────────────────────────────────────────────────────

CONFTEST = """
# conftest.py — pytest fixtures available to all tests
import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, ProductFactory, CategoryFactory


@pytest.fixture(scope="session")
def django_db_setup():
    \"\"\"Session-scoped DB — migrations run once per test session.\"\"\"
    pass


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin(db):
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin):
    api_client.force_authenticate(user=admin)
    return api_client


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def products(db, category):
    return ProductFactory.create_batch(5, category=category)


# Override settings for specific tests
@pytest.fixture
def with_cache(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
"""

print("Testing module loaded. Key patterns:")
print("  - Factory Boy for fixtures")
print("  - pytest-django for database access")
print("  - patch() for mocking external services")
print("  - Parametrize for testing multiple inputs")
