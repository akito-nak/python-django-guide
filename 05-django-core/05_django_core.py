"""
============================================================
05 - DJANGO CORE: Settings, Apps, Middleware & URLs
============================================================
Django follows the "batteries included" philosophy — it comes
with everything you need for a production web app out of the box:
ORM, auth, admin, forms, caching, sessions, and more.

The architecture: Request → Middleware → URL Router → View →
                  Model/Template → Response → Middleware → Client
============================================================
"""

# ─────────────────────────────────────────────────────────────
# PROJECT STRUCTURE
# ─────────────────────────────────────────────────────────────
# django-admin startproject myproject
# python manage.py startapp users
#
# myproject/
# ├── manage.py                  ← CLI entry point
# ├── myproject/
# │   ├── __init__.py
# │   ├── settings/              ← settings package (better than one file)
# │   │   ├── __init__.py
# │   │   ├── base.py            ← shared across all environments
# │   │   ├── development.py     ← local dev overrides
# │   │   └── production.py      ← production overrides
# │   ├── urls.py                ← root URL configuration
# │   ├── wsgi.py                ← WSGI server entry point
# │   └── asgi.py                ← ASGI server entry point (async)
# ├── users/                     ← a Django "app"
# │   ├── __init__.py
# │   ├── apps.py                ← AppConfig
# │   ├── models.py              ← database models
# │   ├── views.py               ← request handlers
# │   ├── urls.py                ← URL patterns for this app
# │   ├── serializers.py         ← DRF serializers
# │   ├── admin.py               ← admin site config
# │   ├── forms.py               ← Django forms
# │   ├── signals.py             ← event handlers
# │   ├── tasks.py               ← Celery async tasks
# │   ├── tests/
# │   │   ├── __init__.py
# │   │   ├── test_models.py
# │   │   ├── test_views.py
# │   │   └── test_serializers.py
# │   └── migrations/            ← database schema versions
# └── requirements/
#     ├── base.txt
#     ├── development.txt
#     └── production.txt


# ─────────────────────────────────────────────────────────────
# settings/base.py — the foundation
# ─────────────────────────────────────────────────────────────

BASE_SETTINGS = '''
import os
from pathlib import Path
from decouple import config  # pip install python-decouple

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ─────────────────────────────────────────────────
# NEVER hardcode secrets — read from environment variables
SECRET_KEY = config("DJANGO_SECRET_KEY")  # required, no default
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=lambda v: v.split(","))

# ── Installed Apps ────────────────────────────────────────────
INSTALLED_APPS = [
    # Django built-ins (order matters for template loading)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party packages
    "rest_framework",              # Django REST Framework
    "rest_framework_simplejwt",   # JWT authentication
    "corsheaders",                 # CORS headers
    "django_filters",              # Filtering for DRF
    "drf_spectacular",             # OpenAPI / Swagger docs

    # Your apps — always listed last
    "users",
    "products",
    "orders",
]

# ── Middleware ─────────────────────────────────────────────────
# Every request and response passes through these in order.
# Request: top → bottom. Response: bottom → top.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # CORS — must be high up
    "whitenoise.middleware.WhiteNoiseMiddleware",     # serve static files in prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "myproject.middleware.RequestTimingMiddleware",   # our custom middleware
    "myproject.middleware.RequestIDMiddleware",       # attach request IDs for logging
]

# ── Database ──────────────────────────────────────────────────
import dj_database_url
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
        conn_max_age=600,        # connection pooling — reuse connections
        conn_health_checks=True,
    )
}

# ── Authentication ─────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"  # ALWAYS set a custom user model before first migration

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "users.backends.EmailBackend",  # allow login with email
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── DRF Configuration ──────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
    "EXCEPTION_HANDLER": "myproject.exceptions.custom_exception_handler",
}

# ── JWT Settings ───────────────────────────────────────────────
from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── Caching ───────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "myproject",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# ── Email ──────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"  # print to console in dev
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = "noreply@myapp.com"

# ── Static & Media Files ───────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Logging ───────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {request_id} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(module)s %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "myproject": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
}

# ── Internationalization ────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True  # ALWAYS True — store datetimes in UTC

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # 64-bit PKs — safe at scale
'''

# ─────────────────────────────────────────────────────────────
# CUSTOM MIDDLEWARE
# ─────────────────────────────────────────────────────────────
# Middleware is a hook into Django's request/response processing.
# Perfect for: logging, auth checks, adding headers, rate limiting.

MIDDLEWARE_EXAMPLES = '''
import time
import uuid
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger("myproject")


class RequestTimingMiddleware:
    """Log the time each request takes."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        # One-time configuration on startup

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Code here runs BEFORE the view
        start_time = time.perf_counter()

        response = self.get_response(request)  # call the view

        # Code here runs AFTER the view
        elapsed = time.perf_counter() - start_time
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(elapsed * 1000, 2),
            }
        )
        response["X-Request-Duration"] = f"{elapsed:.4f}s"
        return response


class RequestIDMiddleware:
    """Attach a unique ID to every request for tracing."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id  # attach to request object
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class MaintenanceModeMiddleware:
    """Block all requests during maintenance."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        from django.conf import settings
        if getattr(settings, "MAINTENANCE_MODE", False):
            if not request.path.startswith("/admin"):  # allow admin through
                return JsonResponse(
                    {"error": "Service temporarily unavailable", "retry_after": 300},
                    status=503
                )
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Optionally handle exceptions before Django's default handling."""
        logger.exception("Unhandled exception", exc_info=exception,
                        extra={"path": request.path})
        return None  # return None to let Django handle it normally
'''

# ─────────────────────────────────────────────────────────────
# URL CONFIGURATION
# ─────────────────────────────────────────────────────────────

URL_EXAMPLES = '''
# myproject/urls.py — root URL config
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/", include([
        path("users/",    include("users.urls")),
        path("products/", include("products.urls")),
        path("orders/",   include("orders.urls")),
        path("auth/",     include("users.auth_urls")),
    ])),

    # API Schema & Docs
    path("api/schema/",   SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",     SpectacularSwaggerUIView.as_view(url_name="schema"), name="swagger-ui"),

    # Health check (for load balancers)
    path("health/", include("health_check.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]


# users/urls.py — app-level URL config
from django.urls import path
from . import views

app_name = "users"  # namespace — reverse URLs with "users:list"

urlpatterns = [
    # ViewSet URLs (registered via router in DRF — see DRF chapter)
    # path("",      views.UserListCreateView.as_view(), name="list"),
    # path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
]


# users/auth_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/",  views.RegisterView.as_view(), name="register"),
    path("login/",     views.LoginView.as_view(), name="login"),
    path("logout/",    views.LogoutView.as_view(), name="logout"),
    path("refresh/",   TokenRefreshView.as_view(), name="token_refresh"),
    path("me/",        views.CurrentUserView.as_view(), name="me"),
    path("password/change/", views.ChangePasswordView.as_view(), name="change-password"),
    path("password/reset/",  views.RequestPasswordResetView.as_view(), name="reset-request"),
    path("password/reset/confirm/", views.ConfirmPasswordResetView.as_view(), name="reset-confirm"),
]
'''

# ─────────────────────────────────────────────────────────────
# APPS CONFIGURATION
# ─────────────────────────────────────────────────────────────

APP_CONFIG_EXAMPLE = '''
# users/apps.py
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "User Management"

    def ready(self) -> None:
        """Called when Django starts. Import signals here."""
        import users.signals  # noqa: F401 — registers signal handlers
'''

print("Django core configuration patterns loaded.")
print("See comments above for full settings, middleware, and URL examples.")
