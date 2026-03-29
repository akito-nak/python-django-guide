"""
============================================================
13 - REAL-WORLD PATTERNS
============================================================
The patterns in this chapter separate hobby projects from
production systems. Celery for async work, Redis for caching,
the service layer pattern, repository pattern, and the
event-driven architecture that makes Django apps scale.

If Chapter 5 was "how Django works," this is "how Django
works in companies that need it to keep working."
============================================================
"""

import logging
from functools import wraps
from typing import Any, Callable
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# THE SERVICE LAYER PATTERN
# ─────────────────────────────────────────────────────────────
# Fat models + thin views is good. But complex business logic
# belongs in a SERVICE layer — not models, not views.
#
# Structure:
#   View  → validates HTTP, calls service, returns response
#   Service → business logic, orchestrates models and tasks
#   Model → data structure + simple queries
#
# This makes services independently testable and reusable.

class UserService:
    """All user-related business logic in one place."""

    def __init__(self, user_repo=None, email_service=None, cache_service=None):
        # Dependency injection — easy to mock in tests
        self.user_repo     = user_repo     # or: self.user_repo = UserRepository()
        self.email_service = email_service
        self.cache_service = cache_service

    def register_user(self, email: str, password: str, name: str) -> dict:
        """
        Register a new user. Orchestrates: validation, creation,
        email sending, analytics tracking.
        """
        email = email.lower().strip()

        # Business rule validation
        # if self.user_repo.email_exists(email):
        #     raise ValueError(f"Email already registered: {email}")

        # Create user
        # user = self.user_repo.create(email=email, password=password, name=name)
        user = {"id": 1, "email": email, "name": name}  # placeholder

        # Fire-and-forget side effects (via Celery)
        # send_welcome_email.delay(user["id"])
        # track_registration_event.delay(user["id"], source="web")

        logger.info("user_registered", extra={"email": email})
        return user

    def get_user_profile(self, user_id: int) -> dict:
        """Fetch user with caching."""
        cache_key = f"user_profile:{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # profile = self.user_repo.get_with_profile(user_id)
        profile = {"id": user_id, "name": "Alice"}  # placeholder

        cache.set(cache_key, profile, timeout=300)  # cache 5 minutes
        return profile

    def deactivate_user(self, user_id: int, reason: str, performed_by_id: int) -> None:
        """
        Deactivate a user account. Complex business logic that touches
        multiple models and fires multiple side effects.
        """
        # user = self.user_repo.get(user_id)
        # if user.is_superuser:
        #     raise PermissionError("Cannot deactivate superusers")

        # user.is_active = False
        # user.deactivated_at = timezone.now()
        # user.deactivation_reason = reason
        # self.user_repo.save(user)

        # Cascade: revoke tokens, cancel subscriptions, notify, audit log
        # revoke_all_tokens.delay(user_id)
        # cancel_active_subscriptions.delay(user_id)
        # send_deactivation_email.delay(user_id)
        # AuditLog.objects.create(action="deactivate_user", target_id=user_id, by_id=performed_by_id)

        # Invalidate cache
        cache.delete(f"user_profile:{user_id}")
        logger.info("user_deactivated", extra={"user_id": user_id, "reason": reason})


# ─────────────────────────────────────────────────────────────
# CELERY — async task queue
# ─────────────────────────────────────────────────────────────
# Move slow work (email, image processing, API calls, reports)
# OUT of the request/response cycle. Users shouldn't wait.
#
# Install: pip install celery redis django-celery-beat
# Run: celery -A myproject worker --loglevel=info
# Run scheduler: celery -A myproject beat --loglevel=info

CELERY_CONFIG = """
# myproject/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings.development")

app = Celery("myproject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # finds tasks.py in all INSTALLED_APPS

# settings.py Celery config:
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60 * 30  # 30 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 25  # soft limit: 25 minutes

# myproject/__init__.py
from .celery import app as celery_app
__all__ = ("celery_app",)
"""

CELERY_TASKS = """
# users/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings

logger = get_task_logger(__name__)


@shared_task(
    bind=True,                    # gives access to `self` (the task instance)
    max_retries=3,
    default_retry_delay=60,       # wait 60s between retries
    autoretry_for=(Exception,),   # auto-retry on any exception
    acks_late=True,               # only ack after task completes (safer)
)
def send_welcome_email(self, user_id: int) -> str:
    from users.models import User
    try:
        user = User.objects.get(pk=user_id)
        send_mail(
            subject="Welcome to MyApp! 🎉",
            message=f"Hi {user.get_full_name()}, thanks for joining!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        logger.info(f"Welcome email sent to {user.email}")
        return f"Email sent to {user.email}"
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found — skipping email")
        return "User not found"
    except Exception as exc:
        logger.warning(f"Email failed, retrying: {exc}")
        raise self.retry(exc=exc)  # retry with exponential backoff


@shared_task
def generate_monthly_report(month: int, year: int) -> dict:
    \"\"\"Long-running task — generates a report, stores it, notifies admins.\"\"\"
    from orders.models import Order
    import json
    from datetime import date
    from django.db.models import Sum, Count, Avg

    orders = Order.objects.filter(
        created_at__year=year,
        created_at__month=month,
    )
    stats = orders.aggregate(
        total_revenue=Sum("total"),
        order_count=Count("id"),
        avg_order_value=Avg("total"),
    )

    # Save report to DB or S3
    # report = Report.objects.create(month=month, year=year, data=stats)

    # Notify admins
    # notify_admins_of_report.delay(report.pk)
    return stats


@shared_task
def process_uploaded_image(image_id: int) -> None:
    \"\"\"Resize and optimize an uploaded image.\"\"\"
    from PIL import Image
    # image = ProductImage.objects.get(pk=image_id)
    # img = Image.open(image.file.path)
    # Create thumbnails, compress, upload to S3
    logger.info(f"Processed image {image_id}")


# Periodic tasks (scheduled jobs) — managed by celery-beat:
# In settings.py:
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "generate-daily-report": {
        "task": "orders.tasks.generate_daily_report",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM every day
    },
    "cleanup-expired-tokens": {
        "task": "users.tasks.cleanup_expired_tokens",
        "schedule": crontab(hour="*/6"),  # every 6 hours
    },
    "send-daily-digest": {
        "task": "notifications.tasks.send_daily_digest",
        "schedule": crontab(hour=9, minute=0, day_of_week="mon-fri"),
    },
}
"""


# ─────────────────────────────────────────────────────────────
# CACHING PATTERNS
# ─────────────────────────────────────────────────────────────

def cached(key_prefix: str, timeout: int = 300, vary_on: list[str] | None = None):
    """Generic caching decorator for any function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from prefix + relevant arguments
            vary_values = [str(kwargs.get(k, "")) for k in (vary_on or [])]
            cache_key = ":".join([key_prefix] + vary_values + [str(args)])
            cache_key = cache_key[:200]  # Redis key length limit

            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            logger.debug(f"Cache miss, stored: {cache_key}")
            return result
        return wrapper
    return decorator


class CacheService:
    """Centralized cache management — know what you've cached."""

    PREFIXES = {
        "user_profile": "user:profile:{user_id}",
        "product_detail": "product:detail:{slug}",
        "product_list": "product:list:{page}:{filters}",
        "category_tree": "category:tree",
        "user_permissions": "user:perms:{user_id}",
    }

    @classmethod
    def get_user_profile(cls, user_id: int) -> dict | None:
        return cache.get(f"user:profile:{user_id}")

    @classmethod
    def set_user_profile(cls, user_id: int, data: dict, timeout: int = 300) -> None:
        cache.set(f"user:profile:{user_id}", data, timeout=timeout)

    @classmethod
    def invalidate_user(cls, user_id: int) -> None:
        """Invalidate all cache entries for a user."""
        keys = [
            f"user:profile:{user_id}",
            f"user:perms:{user_id}",
        ]
        cache.delete_many(keys)

    @classmethod
    def invalidate_product(cls, slug: str) -> None:
        """When a product changes, clear all related cache."""
        cache.delete(f"product:detail:{slug}")
        # Also clear list pages that might contain this product
        # (harder — use cache versioning or tag-based invalidation)
        cache.delete_pattern("product:list:*")  # requires django-redis


# ─────────────────────────────────────────────────────────────
# SIGNALS — decouple side effects
# ─────────────────────────────────────────────────────────────

SIGNALS_PATTERNS = """
# The Right Way to Use Signals:
# ✅ Auto-create related objects (UserProfile on User creation)
# ✅ Clear cache when data changes
# ✅ Async side effects (fire tasks)
# ❌ Don't put core business logic in signals — hard to trace, test, order

# users/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    if created:
        # Auto-create profile
        from users.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)
        # Fire async welcome email
        from users.tasks import send_welcome_email
        send_welcome_email.delay(instance.pk)

@receiver(post_save, sender=User)
def on_user_saved(sender, instance, **kwargs):
    # Invalidate cache on any save
    from myproject.cache import CacheService
    CacheService.invalidate_user(instance.pk)

@receiver(post_delete, sender=User)
def on_user_deleted(sender, instance, **kwargs):
    CacheService.invalidate_user(instance.pk)
    # Trigger cleanup tasks
    from users.tasks import cleanup_user_data
    cleanup_user_data.delay(instance.pk)
"""


# ─────────────────────────────────────────────────────────────
# REPOSITORY PATTERN — abstract data access
# ─────────────────────────────────────────────────────────────

class BaseRepository:
    """Generic repository — wraps Django ORM."""
    model = None

    def get(self, **kwargs):
        return self.model.objects.get(**kwargs)

    def get_or_none(self, **kwargs):
        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def filter(self, **kwargs):
        return self.model.objects.filter(**kwargs)

    def create(self, **kwargs):
        return self.model.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()) + ["updated_at"])
        return instance

    def delete(self, instance):
        instance.delete()

    def bulk_create(self, objects: list, batch_size: int = 100):
        return self.model.objects.bulk_create(objects, batch_size=batch_size)


class ProductRepository(BaseRepository):
    """Product-specific data access."""
    # model = Product

    def get_active(self):
        return self.model.objects.filter(is_active=True, deleted_at__isnull=True)

    def get_by_slug(self, slug: str):
        return self.get_or_none(slug=slug, is_active=True)

    def search(self, query: str, category_slug: str | None = None):
        from django.db.models import Q
        qs = self.get_active()
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs.select_related("category").prefetch_related("tags")

    def get_featured(self, limit: int = 10):
        return self.get_active().filter(is_featured=True).order_by("-created_at")[:limit]


# ─────────────────────────────────────────────────────────────
# RATE LIMITING & THROTTLING (custom Redis-based)
# ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Redis-backed rate limiter using a sliding window."""

    def __init__(self, key_prefix: str, limit: int, window_seconds: int):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window_seconds

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if the identifier is within the rate limit.
        Returns: (is_allowed, remaining_calls)
        """
        import time
        key = f"ratelimit:{self.key_prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window

        # Use Redis sorted sets for sliding window
        # pipeline = cache.client.pipeline()  # using django-redis
        # pipeline.zremrangebyscore(key, 0, window_start)  # remove old requests
        # pipeline.zadd(key, {str(now): now})              # add this request
        # pipeline.zcard(key)                              # count in window
        # pipeline.expire(key, self.window)                # set TTL
        # _, _, count, _ = pipeline.execute()

        count = 0  # placeholder
        remaining = max(0, self.limit - count)
        return count <= self.limit, remaining


# Usage in a view:
login_limiter = RateLimiter("login", limit=5, window_seconds=60)

def rate_limited_login(request):
    ip = request.META.get("REMOTE_ADDR", "unknown")
    allowed, remaining = login_limiter.is_allowed(ip)
    if not allowed:
        from django.http import JsonResponse
        return JsonResponse(
            {"error": "Too many login attempts. Try again in 60 seconds."},
            status=429,
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"}
        )
    # ... proceed with login


# ─────────────────────────────────────────────────────────────
# FEATURE FLAGS — deploy safely
# ─────────────────────────────────────────────────────────────

FEATURE_FLAGS = """
# Simple feature flag system using Django settings + cache
# For production use: Unleash, LaunchDarkly, or django-waffle

class FeatureFlag:
    def __init__(self, name: str, default: bool = False):
        self.name = name
        self.default = default

    def is_enabled(self, user=None) -> bool:
        # Check cache first
        cache_key = f"feature:{self.name}"
        if user:
            cache_key += f":user:{user.pk}"

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Check DB
        # try:
        #     flag = FeatureFlagModel.objects.get(name=self.name)
        #     if user and flag.user_rollout_percent:
        #         # Percentage rollout — deterministic based on user ID
        #         import hashlib
        #         hash_val = int(hashlib.md5(f"{self.name}:{user.pk}".encode()).hexdigest(), 16)
        #         enabled = (hash_val % 100) < flag.user_rollout_percent
        #     else:
        #         enabled = flag.is_enabled
        # except FeatureFlagModel.DoesNotExist:
        #     enabled = self.default

        enabled = self.default
        cache.set(cache_key, enabled, timeout=60)
        return enabled

# Define flags in one place:
NEW_CHECKOUT = FeatureFlag("new_checkout", default=False)
AI_SEARCH    = FeatureFlag("ai_search", default=False)
DARK_MODE    = FeatureFlag("dark_mode", default=True)

# Use in views:
def checkout(request):
    if NEW_CHECKOUT.is_enabled(user=request.user):
        return render(request, "checkout/new.html")
    return render(request, "checkout/legacy.html")
"""

print("Real-world patterns loaded:")
print("  - Service layer pattern")
print("  - Celery async tasks + periodic jobs")
print("  - Caching with invalidation strategies")
print("  - Repository pattern")
print("  - Rate limiting")
print("  - Feature flags")
