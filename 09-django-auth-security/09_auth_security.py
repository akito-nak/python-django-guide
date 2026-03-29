"""
============================================================
09 - DJANGO AUTH & SECURITY
============================================================
Security isn't a feature — it's a foundation. Django gives
you excellent security primitives out of the box, but you
still need to configure and use them correctly.

Topics: JWT auth flow, custom backends, permissions,
throttling, input validation, security headers, and the
most common vulnerabilities to guard against.
============================================================
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# CUSTOM AUTHENTICATION BACKEND
# ─────────────────────────────────────────────────────────────
# Django's default backend authenticates by username.
# We want email login. Add to settings:
# AUTHENTICATION_BACKENDS = ["users.backends.EmailBackend"]

class EmailBackend(BaseBackend):
    """Allow users to log in with their email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # username param may contain an email (Django passes whatever
        # the login form submits as "username")
        email = kwargs.get("email", username)
        if not email or not password:
            return None

        try:
            # User = get_user_model()
            # user = User.objects.get(email=email.lower())
            user = None  # placeholder
        except Exception:
            # Run the default password hasher to prevent timing attacks
            # — if we return immediately for unknown emails, an attacker
            # can enumerate valid email addresses by measuring response time
            # User().set_password(password)  # dummy hash
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            # User = get_user_model()
            # return User.objects.get(pk=user_id)
            return None
        except Exception:
            return None

    def user_can_authenticate(self, user) -> bool:
        """Only allow active users to authenticate."""
        return getattr(user, "is_active", False)


# ─────────────────────────────────────────────────────────────
# JWT AUTH VIEWS
# ─────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email        = serializers.EmailField()
    password     = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name   = serializers.CharField(max_length=150)
    last_name    = serializers.CharField(max_length=150)

    def validate_email(self, value: str) -> str:
        value = value.lower().strip()
        # if User.objects.filter(email=value).exists():
        #     raise serializers.ValidationError("Email already registered.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        # Optionally validate password strength here
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # user = User.objects.create_user(password=password, **validated_data)
        # return user
        return validated_data  # placeholder


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens immediately on registration
        # refresh = RefreshToken.for_user(user)
        # Send verification email
        # send_verification_email.delay(user.pk)  # async via Celery

        logger.info("user_registered", extra={"email": request.data.get("email")})

        return Response({
            "message": "Registration successful. Please verify your email.",
            # "access": str(refresh.access_token),
            # "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get("email", "").lower().strip()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)
        if not user:
            logger.warning("login_failed", extra={"email": email, "ip": self._get_ip(request)})
            # Return the same message for wrong email AND wrong password
            # — never reveal which one is wrong (user enumeration attack)
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response({"error": "Account is disabled."}, status=status.HTTP_403_FORBIDDEN)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        # Add custom claims to the token
        refresh["email"] = user.email
        refresh["is_staff"] = user.is_staff

        # Update last login
        # user.last_login = timezone.now()
        # user.save(update_fields=["last_login"])

        logger.info("user_logged_in", extra={"user_id": user.pk})

        return Response({
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes in seconds
        })

    def _get_ip(self, request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required."}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # requires rest_framework_simplejwt.token_blacklist in INSTALLED_APPS
        except TokenError as e:
            return Response({"error": str(e)}, status=400)
        return Response({"message": "Logged out successfully."})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current  = request.data.get("current_password", "")
        new_pass = request.data.get("new_password", "")
        confirm  = request.data.get("new_password_confirm", "")

        if not request.user.check_password(current):
            return Response({"error": "Current password is incorrect."}, status=400)
        if new_pass != confirm:
            return Response({"error": "New passwords do not match."}, status=400)
        if len(new_pass) < 8:
            return Response({"error": "Password must be at least 8 characters."}, status=400)

        request.user.set_password(new_pass)
        request.user.save(update_fields=["password"])

        logger.info("password_changed", extra={"user_id": request.user.pk})
        return Response({"message": "Password changed successfully."})


# ─────────────────────────────────────────────────────────────
# EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────────

EMAIL_VERIFICATION = """
# Use signed tokens — no need to store verification tokens in the DB!
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings

signer = TimestampSigner()

def send_verification_email(user) -> None:
    token = signer.sign(user.pk)  # signed + timestamped
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject="Verify your email address",
        message=f"Click to verify: {link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        try:
            user_pk = signer.unsign(token, max_age=86400)  # 24 hours
        except SignatureExpired:
            return Response({"error": "Verification link has expired."}, status=400)
        except BadSignature:
            return Response({"error": "Invalid verification token."}, status=400)

        # User = get_user_model()
        # user = get_object_or_404(User, pk=user_pk)
        # user.is_verified = True
        # user.save(update_fields=["is_verified"])
        return Response({"message": "Email verified successfully."})
"""


# ─────────────────────────────────────────────────────────────
# PERMISSIONS — fine-grained access control
# ─────────────────────────────────────────────────────────────

PERMISSIONS_GUIDE = """
# Django has two levels of permissions:

# 1. MODEL-LEVEL permissions (built into Django admin)
#    Auto-created for every model: add_product, change_product, delete_product, view_product
#    Assign to users via groups or directly

# 2. OBJECT-LEVEL permissions — per-object access
#    Django doesn't do this out of the box.
#    Use django-guardian or implement in your views.

# Assigning permissions in code:
from django.contrib.auth.models import Permission, Group

# To a user:
permission = Permission.objects.get(codename="change_product")
user.user_permissions.add(permission)

# To a group:
editors = Group.objects.create(name="Editors")
editors.permissions.set([
    Permission.objects.get(codename="add_product"),
    Permission.objects.get(codename="change_product"),
    Permission.objects.get(codename="view_product"),
])
user.groups.add(editors)

# Checking in views:
@login_required
@permission_required("products.change_product", raise_exception=True)
def edit_product(request, pk):
    ...

# Checking in templates:
# {% if perms.products.change_product %}
#     <a href="{% url 'products:edit' pk=product.pk %}">Edit</a>
# {% endif %}

# Custom permission:
class IsProductOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user or request.user.is_staff
"""


# ─────────────────────────────────────────────────────────────
# SECURITY HEADERS & DJANGO SETTINGS
# ─────────────────────────────────────────────────────────────

SECURITY_SETTINGS = """
# settings/production.py — security settings for production

# Force HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS — tell browsers to always use HTTPS for this domain
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True            # only send session cookie over HTTPS
SESSION_COOKIE_HTTPONLY = True          # JS can't access session cookie
SESSION_COOKIE_SAMESITE = "Lax"        # prevent CSRF in most cases
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Clickjacking protection
X_FRAME_OPTIONS = "DENY"               # don't allow embedding in iframes

# Content type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS filter (legacy browsers)
SECURE_BROWSER_XSS_FILTER = True

# Referrer policy
SECURE_REFERRER_POLICY = "same-origin"

# CORS (django-cors-headers)
CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",
    "https://www.myapp.com",
]
CORS_ALLOW_CREDENTIALS = True  # if you use cookies for auth
CORS_ALLOWED_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "dnt", "origin", "user-agent",
    "x-csrftoken", "x-requested-with",
]
"""


# ─────────────────────────────────────────────────────────────
# THROTTLING — protect against abuse
# ─────────────────────────────────────────────────────────────

THROTTLING_EXAMPLE = """
# Custom throttle classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    # Strict: max 5 login attempts per minute per IP
    rate = "5/min"
    scope = "login"

class AIQueryThrottle(UserRateThrottle):
    # AI calls are expensive — 20/day per user
    rate = "20/day"
    scope = "ai_query"

class BurstRateThrottle(UserRateThrottle):
    # Allow bursts: 30 requests/minute
    rate = "30/min"
    scope = "burst"

class SustainedRateThrottle(UserRateThrottle):
    # But not sustained: 300 requests/hour
    rate = "300/hour"
    scope = "sustained"

# In views:
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]

class ProductViewSet(viewsets.ModelViewSet):
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]

# In settings:
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
        "ai_query": "20/day",
        "burst": "30/min",
        "sustained": "300/hour",
        "anon": "100/day",
        "user": "1000/day",
    }
}
"""


# ─────────────────────────────────────────────────────────────
# COMMON VULNERABILITIES & HOW DJANGO PREVENTS THEM
# ─────────────────────────────────────────────────────────────

SECURITY_GUIDE = """
╔══════════════════════════════════════════════════════════════╗
║              OWASP TOP 10 — Django's Defenses                ║
╚══════════════════════════════════════════════════════════════╝

1. INJECTION (SQL Injection)
   ✅ Django ORM uses parameterized queries by default
   ❌ NEVER do: Product.objects.raw(f"SELECT * WHERE name='{name}'")
   ✅ DO:        Product.objects.raw("SELECT * WHERE name=%s", [name])
   ✅ BETTER:    Product.objects.filter(name=name)

2. BROKEN AUTHENTICATION
   ✅ Use Django's auth system, never roll your own
   ✅ JWT with short expiry (15 min access, 7 day refresh)
   ✅ Blacklist refresh tokens on logout
   ✅ Throttle login attempts
   ✅ Use HTTPS only (SECURE_SSL_REDIRECT = True)

3. SENSITIVE DATA EXPOSURE
   ✅ Never log passwords, tokens, or PII
   ✅ Use environment variables for secrets (never hardcode)
   ✅ Encrypt sensitive DB fields (django-encrypted-fields)
   ✅ Use .gitignore to keep .env out of git

4. XML EXTERNAL ENTITIES (XXE)
   ✅ Use defusedxml if you must parse XML
   ✅ Prefer JSON

5. BROKEN ACCESS CONTROL
   ✅ Check permissions on EVERY endpoint, not just the UI
   ✅ Use object-level permissions for user data
   ❌ NEVER trust client-supplied IDs without authorization:
      product = Product.objects.get(id=request.data["id"])  # ❌
      product = get_object_or_404(Product, id=request.data["id"],
                                  owner=request.user)         # ✅

6. SECURITY MISCONFIGURATION
   ✅ DEBUG = False in production
   ✅ SECRET_KEY from environment variable
   ✅ ALLOWED_HOSTS configured
   ✅ Remove unused apps and middleware

7. CROSS-SITE SCRIPTING (XSS)
   ✅ Django templates auto-escape HTML by default
   ❌ NEVER use {{ value|safe }} on user input
   ✅ Use Content Security Policy headers

8. INSECURE DESERIALIZATION
   ✅ Never use pickle for user data
   ✅ Use DRF serializers for all input validation
   ✅ Validate and whitelist accepted content types

9. COMPONENTS WITH KNOWN VULNERABILITIES
   ✅ Run: pip audit  (check for vulnerable packages)
   ✅ Use Dependabot or Snyk
   ✅ Keep Django and dependencies up to date

10. INSUFFICIENT LOGGING
    ✅ Log all auth events (login, logout, failed attempts)
    ✅ Log permission denials
    ✅ Use structured logging (JSON format)
    ✅ Ship logs to a central system (Datadog, CloudWatch, etc.)
    ❌ NEVER log passwords, tokens, or full credit card numbers
"""

print("Auth & Security module loaded.")
print("Key concepts: JWT flow, email verification, permissions, OWASP top 10")
