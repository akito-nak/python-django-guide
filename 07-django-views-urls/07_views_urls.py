"""
============================================================
07 - DJANGO VIEWS & URLS
============================================================
Views are where HTTP requests become responses. Django gives
you two flavors: Function-Based Views (FBVs) for simplicity
and Class-Based Views (CBVs) for reuse. Know both — real
projects use both.

URL patterns connect URLs to views. Get this routing layer
right and the rest of your app flows naturally.
============================================================
"""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.db.models import Q
import json
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# FUNCTION-BASED VIEWS (FBVs)
# ─────────────────────────────────────────────────────────────
# Simple, explicit, easy to read. Great for one-off views
# and anything that doesn't fit CBV patterns neatly.

@require_GET   # returns 405 Method Not Allowed for non-GET requests
@cache_page(60 * 15)  # cache the response for 15 minutes
def product_list(request: HttpRequest) -> HttpResponse:
    """List products with filtering, searching, and pagination."""
    # --- Query params ---
    query    = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort     = request.GET.get("sort", "-created_at")
    page_num = request.GET.get("page", 1)

    # --- Build queryset ---
    # products = Product.objects.active().select_related("category")
    products = []  # placeholder

    if query:
        products = [p for p in products if query.lower() in str(p).lower()]
        # Real: products = products.filter(
        #     Q(name__icontains=query) | Q(description__icontains=query)
        # )

    if category:
        pass  # products = products.filter(category__slug=category)

    # --- Paginate ---
    paginator = Paginator(products, 20)
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    context = {
        "products": page,
        "query": query,
        "category": category,
        "total_count": paginator.count,
    }
    return render(request, "products/list.html", context)


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Show a single product. Returns 404 if not found."""
    # get_object_or_404 is your best friend — raises Http404 instead of crashing
    # product = get_object_or_404(
    #     Product.objects.select_related("category").prefetch_related("tags"),
    #     slug=slug,
    #     is_active=True
    # )
    context = {"slug": slug}
    return render(request, "products/detail.html", context)


@login_required  # redirects to LOGIN_URL if not authenticated
@require_http_methods(["GET", "POST"])
def create_product(request: HttpRequest) -> HttpResponse:
    """Handle product creation form."""
    if request.method == "POST":
        # form = ProductForm(request.POST, request.FILES)
        # if form.is_valid():
        #     product = form.save(commit=False)
        #     product.created_by = request.user
        #     product.save()
        #     messages.success(request, "Product created successfully!")
        #     return redirect("products:detail", slug=product.slug)
        pass
    else:
        pass  # form = ProductForm()

    return render(request, "products/create.html", {})


# ─────────────────────────────────────────────────────────────
# JSON / API FBVs (before you reach for DRF)
# ─────────────────────────────────────────────────────────────

def api_health(request: HttpRequest) -> JsonResponse:
    """Simple health check endpoint."""
    from django.db import connection
    from django.core.cache import cache

    checks = {"status": "ok", "checks": {}}

    # Database check
    try:
        connection.ensure_connection()
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {e}"
        checks["status"] = "degraded"

    # Cache check
    try:
        cache.set("health_check", "ok", 5)
        assert cache.get("health_check") == "ok"
        checks["checks"]["cache"] = "ok"
    except Exception as e:
        checks["checks"]["cache"] = f"error: {e}"

    status_code = 200 if checks["status"] == "ok" else 503
    return JsonResponse(checks, status=status_code)


@require_http_methods(["GET", "POST"])
def api_products(request: HttpRequest) -> JsonResponse:
    """Simple JSON API without DRF."""
    if request.method == "GET":
        # products = list(Product.objects.values("id", "name", "price", "stock"))
        products = [{"id": 1, "name": "Sample", "price": 9.99, "stock": 10}]
        return JsonResponse({"results": products, "count": len(products)})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Validate
        errors = {}
        if not data.get("name"):
            errors["name"] = "Name is required"
        if not data.get("price") or float(data.get("price", 0)) <= 0:
            errors["price"] = "Price must be positive"
        if errors:
            return JsonResponse({"errors": errors}, status=400)

        # Create
        # product = Product.objects.create(**data)
        return JsonResponse({"id": 999, "name": data["name"]}, status=201)


# ─────────────────────────────────────────────────────────────
# CLASS-BASED VIEWS (CBVs)
# ─────────────────────────────────────────────────────────────
# CBVs shine for standard CRUD operations. Less code, more
# reusability through mixins. Trade-off: the magic can be
# harder to follow — always read the source.

class ProductListView(ListView):
    """
    Handles: GET /products/
    Automatically: paginates, provides object_list in context
    """
    # model = Product
    template_name = "products/list.html"
    context_object_name = "products"    # name in template (default: object_list)
    paginate_by = 20
    ordering = ["-created_at"]

    def get_queryset(self):
        """Override to add filtering."""
        qs = super().get_queryset()
        # qs = Product.objects.active().select_related("category")
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        """Add extra data to the template context."""
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["total_count"] = self.get_queryset().count()
        # context["categories"] = Category.objects.annotate(product_count=Count("products"))
        return context


class ProductDetailView(DetailView):
    """Handles: GET /products/<slug:slug>/"""
    # model = Product
    template_name = "products/detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return super().get_queryset().select_related("category").prefetch_related("tags")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Log view, update view count, etc.
        logger.info("product_viewed", extra={"product_id": getattr(obj, 'pk', None),
                                              "user_id": self.request.user.pk})
        return obj


class ProductCreateView(LoginRequiredMixin, CreateView):
    """Handles: GET+POST /products/new/"""
    # model = Product
    # form_class = ProductForm
    template_name = "products/form.html"
    success_url = reverse_lazy("products:list")

    # LoginRequiredMixin redirects to login if not authenticated
    login_url = "/auth/login/"
    redirect_field_name = "next"

    def form_valid(self, form):
        """Called when form is valid. Inject extra data before saving."""
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # messages.success(self.request, f"'{self.object.name}' created!")
        return response

    def form_invalid(self, form):
        logger.warning("product_create_failed", extra={"errors": form.errors})
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Handles: GET+POST /products/<slug:slug>/edit/"""
    # model = Product
    # form_class = ProductForm
    template_name = "products/form.html"
    permission_required = "products.change_product"

    def get_success_url(self):
        return reverse("products:detail", kwargs={"slug": self.object.slug})

    def get_queryset(self):
        """Only allow editing your own products (unless admin)."""
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(created_by=self.request.user)
        return qs


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Handles: GET+POST /products/<slug:slug>/delete/ """
    # model = Product
    template_name = "products/confirm_delete.html"
    success_url = reverse_lazy("products:list")

    def form_valid(self, form):
        """Override to soft-delete instead of hard-delete."""
        self.object = self.get_object()
        self.object.soft_delete(user=self.request.user)
        # messages.success(self.request, "Product deleted.")
        return redirect(self.success_url)


# ─────────────────────────────────────────────────────────────
# CUSTOM MIXINS — reusable view behaviour
# ─────────────────────────────────────────────────────────────

class AjaxRequiredMixin:
    """Reject non-AJAX requests."""
    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "AJAX required"}, status=400)
        return super().dispatch(request, *args, **kwargs)


class OwnershipMixin:
    """Only allow the object owner (or staff) to access."""
    owner_field = "created_by"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        owner = getattr(obj, self.owner_field, None)
        if owner != self.request.user and not self.request.user.is_staff:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to access this resource.")
        return obj


class JsonResponseMixin:
    """Return JSON instead of HTML for CBVs."""
    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(self.get_data(context), **response_kwargs)

    def get_data(self, context):
        return {}


# ─────────────────────────────────────────────────────────────
# ASYNC VIEWS (Django 4.1+)
# ─────────────────────────────────────────────────────────────
# Django supports async views natively. Use them when you have
# I/O-bound work (external APIs, multiple DB queries, etc.)

import asyncio

async def async_dashboard(request: HttpRequest) -> JsonResponse:
    """Run multiple queries concurrently."""
    # These run concurrently — not sequentially!
    # user_count, product_count, order_count = await asyncio.gather(
    #     User.objects.acount(),
    #     Product.objects.acount(),
    #     Order.objects.acount(),
    # )
    await asyncio.sleep(0)  # yield to event loop (placeholder)
    return JsonResponse({
        "users": 0,
        "products": 0,
        "orders": 0,
    })


async def async_external_data(request: HttpRequest) -> JsonResponse:
    """Call an external API asynchronously."""
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("https://api.example.com/data")
            response.raise_for_status()
            return JsonResponse(response.json())
        except httpx.TimeoutException:
            return JsonResponse({"error": "Request timed out"}, status=504)
        except httpx.HTTPStatusError as e:
            return JsonResponse({"error": str(e)}, status=502)


# ─────────────────────────────────────────────────────────────
# URL CONFIGURATION
# ─────────────────────────────────────────────────────────────

URL_PATTERNS = """
# products/urls.py
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    # Function-based views
    path("",                    views.product_list,   name="list"),
    path("<slug:slug>/",        views.product_detail, name="detail"),
    path("new/",                views.create_product, name="create"),

    # Class-based views (same URLs, different implementation)
    # path("",             views.ProductListView.as_view(),   name="list"),
    # path("<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    # path("new/",         views.ProductCreateView.as_view(), name="create"),
    # path("<slug:slug>/edit/",   views.ProductUpdateView.as_view(), name="update"),
    # path("<slug:slug>/delete/", views.ProductDeleteView.as_view(), name="delete"),

    # API endpoints
    path("api/",         views.api_products, name="api-list"),
    path("health/",      views.api_health,   name="health"),
]


# URL patterns reference:
#   path("users/",           ...)  # exact match: /users/
#   path("users/<int:pk>/",  ...)  # int converter
#   path("posts/<slug:slug>/", ...) # slug converter
#   path("files/<path:filepath>", ...) # path converter (includes /)
#   path("items/<uuid:id>/", ...)   # UUID converter
#   re_path(r"^legacy/(?P<id>[0-9]+)/$", ...)  # regex (use sparingly)

# URL reversing — never hardcode URLs in code:
#   reverse("products:detail", kwargs={"slug": "my-product"})
#   In templates: {% url 'products:detail' slug=product.slug %}
"""
