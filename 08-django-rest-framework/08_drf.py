"""
============================================================
08 - DJANGO REST FRAMEWORK (DRF)
============================================================
DRF is the gold standard for building REST APIs in Python.
It provides: serializers (data validation + transformation),
viewsets (request handling), routers (URL generation),
authentication, permissions, pagination, filtering, and more.

This is what makes Django competitive with FastAPI for APIs.
============================================================
"""

from rest_framework import serializers, viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView
)
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django_filters import rest_framework as django_filters
from django.db.models import Q, Prefetch, Avg, Count
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# SERIALIZERS — validate input, control output
# ─────────────────────────────────────────────────────────────
# Serializers do two things:
#   1. Deserialize: validate incoming JSON → Python objects
#   2. Serialize: Python objects → JSON for responses
# Separate input and output serializers when their shapes differ.

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)  # from annotation

    class Meta:
        model = None  # would be: model = Category
        fields = ["id", "name", "slug", "product_count"]
        read_only_fields = ["id", "slug"]  # computed/auto fields


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


# Input serializer — what we accept from clients
class ProductCreateSerializer(serializers.ModelSerializer):
    """Accepts category_id and tag IDs, validates everything."""
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=None,  # would be: queryset=Tag.objects.all()
        required=False, write_only=True,
        source="tags"  # maps to the Product.tags M2M field
    )

    class Meta:
        model = None  # Product
        fields = [
            "name", "description", "price", "stock",
            "category", "tag_ids", "metadata"
        ]

    def validate_price(self, value):
        """Field-level validation — method name must be validate_<fieldname>."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        """Object-level validation — runs after all field validations pass."""
        # Example: if in_stock is True, stock must be > 0
        if attrs.get("stock", 0) == 0 and attrs.get("is_active", True):
            # We could raise or just warn
            pass
        return attrs

    def create(self, validated_data):
        """Override to handle M2M fields (they can't be set via .create() normally)."""
        tags = validated_data.pop("tags", [])
        product = super().create(validated_data)
        product.tags.set(tags)  # M2M can only be set after the object is saved
        return product

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        product = super().update(instance, validated_data)
        if tags is not None:  # only update if provided (PATCH support)
            product.tags.set(tags)
        return product


# Output serializer — what we send to clients
class ProductDetailSerializer(serializers.ModelSerializer):
    """Rich, nested output representation."""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = None  # Product
        fields = [
            "id", "name", "slug", "description",
            "price", "discounted_price", "stock", "in_stock",
            "category", "tags", "metadata",
            "created_at", "updated_at"
        ]

    def get_discounted_price(self, obj) -> float | None:
        """SerializerMethodField — custom computed field."""
        # Could apply a discount from context, request user, etc.
        request = self.context.get("request")
        if request and hasattr(request.user, "discount_rate"):
            return float(obj.price * (1 - request.user.discount_rate))
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """Lighter representation for list views."""
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = None  # Product
        fields = ["id", "name", "slug", "price", "in_stock", "category_name"]


# User serializers
class UserRegistrationSerializer(serializers.Serializer):
    """Not a ModelSerializer — full manual control."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        min_length=8
    )
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value: str) -> str:
        # Dynamic import to avoid circular imports in this demo file
        # User = get_user_model()
        # if User.objects.filter(email=value.lower()).exists():
        #     raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # user = User.objects.create_user(password=password, **validated_data)
        # return user
        return validated_data  # placeholder


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = None  # User
        fields = ["id", "email", "first_name", "last_name", "full_name",
                  "is_verified", "date_joined", "profile"]
        read_only_fields = ["id", "email", "is_verified", "date_joined"]

    def get_full_name(self, obj) -> str:
        return f"{obj.get('first_name', '')} {obj.get('last_name', '')}".strip()

    def get_profile(self, obj) -> dict | None:
        # In reality: return UserProfileSerializer(obj.profile).data if hasattr(obj, 'profile') else None
        return None


# ─────────────────────────────────────────────────────────────
# PERMISSIONS — who can do what
# ─────────────────────────────────────────────────────────────

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to everyone, but only allow writes to the object's owner.
    """
    def has_object_permission(self, request, view, obj) -> bool:
        # Safe methods (GET, HEAD, OPTIONS) are always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only if the object belongs to the request user
        return obj.owner == request.user


class IsVerifiedUser(permissions.BasePermission):
    """Only verified users can access this endpoint."""
    message = "Your account must be verified to perform this action."

    def has_permission(self, request, view) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, "is_verified", False)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins can do anything; everyone else is read-only."""
    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class HasAPIKey(permissions.BasePermission):
    """Check for a custom API key header."""
    def has_permission(self, request, view) -> bool:
        from django.conf import settings
        api_key = request.headers.get("X-API-Key")
        return api_key in getattr(settings, "VALID_API_KEYS", [])


# ─────────────────────────────────────────────────────────────
# FILTERS — flexible queryset filtering
# ─────────────────────────────────────────────────────────────

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category  = django_filters.CharFilter(field_name="category__slug")
    tag       = django_filters.CharFilter(field_name="tags__slug", method="filter_by_tag")
    in_stock  = django_filters.BooleanFilter(method="filter_in_stock")
    created_after  = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = None  # Product
        fields = ["is_active", "category", "min_price", "max_price"]

    def filter_by_tag(self, queryset, name, value):
        return queryset.filter(tags__slug=value).distinct()

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)


# ─────────────────────────────────────────────────────────────
# PAGINATION
# ─────────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"  # ?page_size=50
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count":    self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "next":     self.get_next_link(),
            "previous": self.get_previous_link(),
            "results":  data,
        })


class SmallPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 50


class CursorPaginationByDate(CursorPagination):
    """Better for real-time feeds — stable pagination even as data changes."""
    ordering = "-created_at"
    page_size = 20


# ─────────────────────────────────────────────────────────────
# VIEWSETS — the cleanest way to build CRUD endpoints
# ─────────────────────────────────────────────────────────────

class ProductViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD for products.
    ModelViewSet provides: list, create, retrieve, update, partial_update, destroy
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "category__name", "tags__name"]
    ordering_fields = ["name", "price", "created_at", "stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = (
            None  # Product.objects.active()
            # .select_related("category")
            # .prefetch_related("tags")
            # .annotate(review_avg=Avg("reviews__rating"), review_count=Count("reviews"))
        )
        # Admins see all products; regular users only see active
        # if not self.request.user.is_staff:
        #     qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == "list":
            return ProductListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductCreateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Called when creating — inject extra data."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete(user=self.request.user)

    # ── Custom actions ─────────────────────────────────────────
    # @action creates non-standard endpoints: /products/{id}/featured/

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def feature(self, request, pk=None):
        """POST /api/v1/products/{id}/feature/ — mark as featured."""
        product = self.get_object()
        # product.is_featured = True
        # product.save(update_fields=["is_featured"])
        return Response({"status": "Product featured successfully"})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def apply_discount(self, request, pk=None):
        """POST /api/v1/products/{id}/apply_discount/ with { "percent": 10 }"""
        product = self.get_object()
        serializer = DiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        percent = serializer.validated_data["percent"]
        # product.apply_discount(percent)
        return Response({
            "message": f"Applied {percent}% discount",
            "new_price": float(100 * (1 - percent/100))  # placeholder
        })

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """GET /api/v1/products/featured/ — list featured products."""
        # qs = Product.objects.featured()[:10]
        # serializer = ProductListSerializer(qs, many=True, context={"request": request})
        # return Response(serializer.data)
        return Response({"featured": []})

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def stats(self, request):
        """GET /api/v1/products/stats/ — aggregate statistics."""
        # stats = Product.objects.aggregate(
        #     total=Count("id"),
        #     active=Count("id", filter=Q(is_active=True)),
        #     avg_price=Avg("price"),
        # )
        return Response({
            "total": 0,
            "active": 0,
            "avg_price": 0.00
        })


class DiscountSerializer(serializers.Serializer):
    percent = serializers.FloatField(min_value=0.1, max_value=99.9)


# ─────────────────────────────────────────────────────────────
# URL ROUTER — auto-generates all URLs for a ViewSet
# ─────────────────────────────────────────────────────────────

ROUTER_SETUP = """
# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")
router.register("categories", views.CategoryViewSet, basename="category")

# This generates:
#   GET/POST   /products/          → list, create
#   GET        /products/featured/ → featured (custom action)
#   GET        /products/stats/    → stats (custom action)
#   GET/PUT/PATCH/DELETE /products/{id}/     → retrieve, update, partial_update, destroy
#   POST       /products/{id}/feature/       → feature (custom action)
#   POST       /products/{id}/apply_discount/ → apply_discount (custom action)

urlpatterns = [path("", include(router.urls))]
"""

# ─────────────────────────────────────────────────────────────
# CUSTOM EXCEPTION HANDLER
# ─────────────────────────────────────────────────────────────

def custom_exception_handler(exc, context):
    """Consistent error responses across the entire API."""
    from rest_framework.views import exception_handler
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.db import IntegrityError

    # Let DRF handle its own exceptions first
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize the error format
        error_data = {
            "status": response.status_code,
            "error": response.status_text,
            "message": _extract_message(response.data),
            "details": response.data if isinstance(response.data, dict) else None,
        }
        response.data = error_data
        return response

    # Handle Django/Python exceptions that DRF doesn't handle
    if isinstance(exc, IntegrityError):
        return Response(
            {"status": 409, "error": "Conflict", "message": str(exc)},
            status=status.HTTP_409_CONFLICT
        )

    # Unexpected exceptions — log them, return 500
    logger.exception("Unexpected error", exc_info=exc,
                     extra={"path": context["request"].path})
    return Response(
        {"status": 500, "error": "Internal Server Error",
         "message": "An unexpected error occurred"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

def _extract_message(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return data[0] if data else "Error"
    if isinstance(data, dict):
        for key in ("detail", "message", "non_field_errors"):
            if key in data:
                return str(data[key])
        first_value = next(iter(data.values()), "Error")
        return str(first_value[0] if isinstance(first_value, list) else first_value)
    return "Error"


# ─────────────────────────────────────────────────────────────
# VIEWSET FOR USERS (auth endpoints)
# ─────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.save()
        # In reality: generate JWT tokens for the new user
        return Response({
            "message": "Registration successful",
            "user": user_data,
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


print("DRF module loaded: serializers, viewsets, permissions, filters, pagination")
