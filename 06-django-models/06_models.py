"""
============================================================
06 - DJANGO MODELS: The ORM in Full Depth
============================================================
Django's ORM lets you define your database schema in Python
and interact with it through objects. No SQL required — though
you can always drop down to raw SQL when needed.

"The ORM is not an abstraction to avoid SQL. It's a tool that
makes the common case easy and the complex case possible."
============================================================
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
import uuid


# ─────────────────────────────────────────────────────────────
# CUSTOM USER MODEL — always do this before your first migration
# ─────────────────────────────────────────────────────────────
# Never use Django's default User if you might want to extend it later.
# Changing it after migrations is painful. Set it up first, always.

class User(AbstractUser):
    """
    Custom user model — use email as the primary login identifier.
    AbstractUser gives us: username, email, password, first_name,
    last_name, is_staff, is_active, date_joined, and all auth logic.
    """
    # Override email to be unique (Django's default allows duplicates!)
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(max_length=150, blank=True)  # optional now

    # Additional fields
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\+?[\d\s\-]{7,15}$", "Enter a valid phone number")]
    )
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # Use email as the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # required by createsuperuser but not login

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active", "is_verified"]),
        ]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_complete(self) -> bool:
        """Has the user completed their profile?"""
        return bool(self.first_name and self.last_name and self.bio)


# ─────────────────────────────────────────────────────────────
# ABSTRACT BASE MODELS — reusable model mixins
# ─────────────────────────────────────────────────────────────
# abstract=True means "don't create a table for me — I'm a mixin"

class TimestampedModel(models.Model):
    """Every model should know when it was created and updated."""
    created_at = models.DateTimeField(auto_now_add=True)  # set on CREATE
    updated_at = models.DateTimeField(auto_now=True)       # set on every SAVE

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """Use UUID as primary key — prevents ID enumeration attacks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Don't actually delete records — just mark them as deleted."""
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        "users.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, user=None) -> None:
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])


# ─────────────────────────────────────────────────────────────
# FIELD TYPES — the most important ones
# ─────────────────────────────────────────────────────────────

class FieldExamples(TimestampedModel, UUIDModel):
    """Showcase of Django field types."""

    # Text fields
    name = models.CharField(max_length=255)            # VARCHAR(255)
    slug = models.SlugField(max_length=255, unique=True)  # URL-safe string
    description = models.TextField(blank=True)         # unlimited text
    secret = models.BinaryField()                      # raw bytes

    # Number fields
    count = models.IntegerField(default=0)
    big_count = models.BigIntegerField(default=0)      # 64-bit
    score = models.FloatField()                        # imprecise!
    price = models.DecimalField(max_digits=10, decimal_places=2)  # exact!
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Boolean
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    # Date/time
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    event_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)  # timedelta

    # Files
    document = models.FileField(upload_to="documents/%Y/%m/")
    image = models.ImageField(upload_to="images/", null=True, blank=True)

    # JSON — store arbitrary structured data
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Choices — use TextChoices for readable, type-safe choices
    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     _("Draft")
        PUBLISHED = "PUBLISHED", _("Published")
        ARCHIVED  = "ARCHIVED",  _("Archived")

    class Priority(models.IntegerChoices):
        LOW    = 1, _("Low")
        MEDIUM = 2, _("Medium")
        HIGH   = 3, _("High")
        URGENT = 4, _("Urgent")

    status   = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)

    class Meta:
        abstract = True  # don't create a real table for this demo


# ─────────────────────────────────────────────────────────────
# RELATIONSHIPS
# ─────────────────────────────────────────────────────────────

class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",                              # self-referential
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="children"
    )

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class Tag(TimestampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Product(TimestampedModel, SoftDeleteModel):
    """
    Product model demonstrating all relationship types.
    """
    # ── ForeignKey — ManyToOne ───────────────────────────────
    # "Many products belong to one category"
    # on_delete options:
    #   CASCADE    — delete product if category deleted
    #   PROTECT    — prevent category deletion if products exist
    #   SET_NULL   — set category to NULL if deleted
    #   SET_DEFAULT — set to default value
    #   DO_NOTHING  — do nothing (dangerous — breaks referential integrity)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,          # don't delete categories with products
        related_name="products",           # category.products.all()
        null=True, blank=True,
    )

    # ── ManyToManyField ──────────────────────────────────────
    # "A product can have many tags; a tag can belong to many products"
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    # ── ManyToMany WITH extra data — use through model ────────
    # "Which stores carry this product, at what price?"
    stores = models.ManyToManyField(
        "Store",
        through="StoreInventory",
        related_name="products"
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name="product_price_non_negative"
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def apply_discount(self, percent: float) -> None:
        if not 0 < percent < 100:
            raise ValueError(f"Discount must be between 0 and 100, got {percent}")
        from decimal import Decimal
        self.price = self.price * (1 - Decimal(str(percent)) / 100)
        self.save(update_fields=["price", "updated_at"])


class Store(TimestampedModel):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class StoreInventory(TimestampedModel):
    """Through model for Product-Store M2M with extra data."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store   = models.ForeignKey(Store, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    local_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = [("product", "store")]

    def __str__(self) -> str:
        return f"{self.product} at {self.store}: {self.quantity}"


# ── OneToOneField ─────────────────────────────────────────────
class UserProfile(TimestampedModel):
    """Extended user data — one profile per user."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="profile"  # user.profile
    )
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)


# ─────────────────────────────────────────────────────────────
# CUSTOM MANAGERS & QUERYSETS
# ─────────────────────────────────────────────────────────────
# Managers encapsulate your query logic — no raw QuerySets scattered
# throughout your views. This is where the "fat model, thin view" pattern shines.

class ProductQuerySet(models.QuerySet):
    """Chainable query methods for Product."""

    def active(self):
        return self.filter(is_active=True, deleted_at__isnull=True)

    def in_stock(self):
        return self.filter(stock__gt=0)

    def by_category(self, category_slug: str):
        return self.filter(category__slug=category_slug)

    def with_discount(self, percent: float):
        """Annotate queryset with discounted price."""
        from decimal import Decimal
        from django.db.models import ExpressionWrapper, F, DecimalField
        multiplier = Decimal(str(1 - percent / 100))
        return self.annotate(
            discounted_price=ExpressionWrapper(
                F("price") * multiplier,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

    def expensive(self, min_price=100):
        return self.filter(price__gte=min_price)

    def with_category_count(self):
        """Annotate with the number of products in the same category."""
        from django.db.models import Count, OuterRef, Subquery
        return self.annotate(
            category_product_count=Count("category__products", distinct=True)
        )

    def recently_updated(self, days=7):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(updated_at__gte=cutoff)


class ProductManager(models.Manager):
    def get_queryset(self) -> ProductQuerySet:
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def in_stock(self):
        return self.get_queryset().in_stock()

    def featured(self):
        return self.get_queryset().active().in_stock().order_by("-created_at")


# Attach manager to Product (in a real app, add directly to the model):
# class Product(TimestampedModel):
#     objects = ProductManager()    # replaces the default manager
#     all_objects = models.Manager()  # includes soft-deleted


# ─────────────────────────────────────────────────────────────
# QUERYSET API — the most important operations
# ─────────────────────────────────────────────────────────────

QUERYSET_EXAMPLES = """
# ── Fetching data ─────────────────────────────────────────────
Product.objects.all()                         # all products (lazy!)
Product.objects.filter(is_active=True)        # WHERE is_active = True
Product.objects.exclude(category=None)        # WHERE category IS NOT NULL
Product.objects.get(id=1)                     # exactly one — raises if 0 or 2+
Product.objects.first()                       # first result or None
Product.objects.last()                        # last result or None
Product.objects.count()                       # SELECT COUNT(*) — efficient!
Product.objects.exists()                      # SELECT EXISTS(...) — most efficient!

# ── Lookups (field__lookup) ───────────────────────────────────
Product.objects.filter(price__gte=100)        # price >= 100
Product.objects.filter(price__lt=50)          # price < 50
Product.objects.filter(price__range=(10, 50)) # BETWEEN 10 AND 50
Product.objects.filter(name__contains="shoe")  # LIKE '%shoe%'
Product.objects.filter(name__icontains="shoe") # case-insensitive LIKE
Product.objects.filter(name__startswith="Air") # LIKE 'Air%'
Product.objects.filter(tags__name="sale")      # join across M2M!
Product.objects.filter(category__name="Shoes") # join across FK!
Product.objects.filter(created_at__year=2024)  # date extraction
Product.objects.filter(created_at__date=date.today())
Product.objects.filter(metadata__color="red")  # JSON field lookup!
Product.objects.filter(id__in=[1, 2, 3])
Product.objects.filter(category__isnull=True)  # IS NULL

# ── Q objects — complex queries with AND/OR/NOT ───────────────
from django.db.models import Q
Product.objects.filter(
    Q(price__lt=50) | Q(is_featured=True)  # OR
)
Product.objects.filter(
    Q(is_active=True) & Q(price__gte=10)   # AND
)
Product.objects.filter(~Q(status="ARCHIVED"))  # NOT

# ── Ordering ──────────────────────────────────────────────────
Product.objects.order_by("name")           # ASC
Product.objects.order_by("-price")         # DESC
Product.objects.order_by("category__name", "-price")  # multiple fields

# ── Selecting fields ──────────────────────────────────────────
Product.objects.values("id", "name", "price")    # returns dicts
Product.objects.values_list("id", flat=True)      # returns flat list of IDs
Product.objects.only("name", "price")             # lazy: load only these fields
Product.objects.defer("description")              # load everything EXCEPT these

# ── Aggregation ───────────────────────────────────────────────
from django.db.models import Avg, Sum, Min, Max, Count, StdDev

Product.objects.aggregate(
    avg_price=Avg("price"),
    total_stock=Sum("stock"),
    min_price=Min("price"),
    max_price=Max("price"),
    count=Count("id"),
)

# ── Annotation — add computed field to each object ────────────
from django.db.models import F, Value, CharField, ExpressionWrapper, DecimalField
from django.db.models.functions import Concat, Upper, Lower, Coalesce

Product.objects.annotate(
    discounted_price=F("price") * 0.9,          # computed column
    full_name=Concat("category__name", Value(" - "), "name"),  # string concat
    upper_name=Upper("name"),
    stock_value=F("price") * F("stock"),        # multiply two fields
)

# ── Grouping ──────────────────────────────────────────────────
from django.db.models import Count
Category.objects.annotate(
    product_count=Count("products"),
    active_count=Count("products", filter=Q(products__is_active=True))
).order_by("-product_count")

# ── Joins (select_related & prefetch_related) ─────────────────
# select_related — SQL JOIN, for ForeignKey/OneToOne (ONE query)
Product.objects.select_related("category")  # loads category in same query

# prefetch_related — separate query + Python join, for M2M/reverse FK
Product.objects.prefetch_related("tags", "stores")

# Combine them
Product.objects.select_related("category").prefetch_related(
    "tags",
    models.Prefetch(
        "storeinventory_set",
        queryset=StoreInventory.objects.select_related("store").filter(quantity__gt=0),
        to_attr="available_inventory",  # store result in .available_inventory
    )
)

# ── Updates ───────────────────────────────────────────────────
Product.objects.filter(is_active=False).update(stock=0)  # bulk update (one query!)
Product.objects.filter(stock__gt=0).update(stock=F("stock") - 1)  # use F() for atomic!
# NOT: product.stock -= 1  # race condition!
# YES: Product.objects.filter(pk=product.pk).update(stock=F("stock") - 1)

# ── Bulk operations ───────────────────────────────────────────
# bulk_create — much faster than saving one by one
products = [Product(name=f"Product {i}", price=i*10) for i in range(100)]
Product.objects.bulk_create(products, batch_size=50)

# bulk_update — update multiple objects, multiple fields
for p in products:
    p.price = p.price * 0.9
Product.objects.bulk_update(products, ["price"], batch_size=50)

# ── Raw SQL — escape hatch when ORM isn't enough ─────────────
products = Product.objects.raw(
    "SELECT * FROM products_product WHERE price > %s", [100]
)
# Or use connection.cursor() for complete control
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM products_product")
    count = cursor.fetchone()[0]
"""

# ─────────────────────────────────────────────────────────────
# SIGNALS — event-driven model hooks
# ─────────────────────────────────────────────────────────────

SIGNALS_EXAMPLE = """
# users/signals.py
from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User, UserProfile

# Auto-create a UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs) -> None:
    if created:
        UserProfile.objects.create(user=instance)
        # Send welcome email
        send_mail(
            subject="Welcome to MyApp!",
            message=f"Hi {instance.get_full_name()}, welcome!",
            from_email="noreply@myapp.com",
            recipient_list=[instance.email],
        )


@receiver(pre_delete, sender=User)
def before_user_delete(sender, instance: User, **kwargs) -> None:
    # Clean up related resources before deletion
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User being deleted: {instance.email}")


# Register signals in users/apps.py:
# class UsersConfig(AppConfig):
#     def ready(self):
#         import users.signals  # noqa
"""

# ─────────────────────────────────────────────────────────────
# MIGRATIONS — version control for your database
# ─────────────────────────────────────────────────────────────

MIGRATIONS_GUIDE = """
# Common migration commands:
# python manage.py makemigrations          — detect model changes, create migration file
# python manage.py migrate                 — apply pending migrations
# python manage.py showmigrations          — list all migrations and status
# python manage.py sqlmigrate users 0001   — show SQL for a migration
# python manage.py migrate users 0002      — migrate to a specific version
# python manage.py migrate users zero      — undo ALL migrations for an app (careful!)

# Custom data migration — when you need to transform data, not just schema
# python manage.py makemigrations --empty users --name=populate_slugs

from django.db import migrations
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    for product in Product.objects.all():
        product.slug = slugify(product.name)
        product.save(update_fields=["slug"])

def reverse_populate_slugs(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.all().update(slug="")

class Migration(migrations.Migration):
    dependencies = [("products", "0001_initial")]
    operations = [
        migrations.RunPython(populate_slugs, reverse_populate_slugs),
    ]
"""

print("Django Models module loaded.")
print("Key patterns: TimestampedModel, SoftDeleteModel, custom managers, Q objects")
