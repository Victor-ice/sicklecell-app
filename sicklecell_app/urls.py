from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (PainEventViewSet, HydrationLogViewSet,
                        LabResultViewSet, risk_today, visit_pdf, insights)
from core.health import health
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r"pain-events", PainEventViewSet, basename="pain-event")
router.register(r"hydrations", HydrationLogViewSet, basename="hydration")
router.register(r"labs", LabResultViewSet, basename="lab")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]

# ...
urlpatterns += [ path("api/risk-today/", risk_today),
                 path("api/visit-pdf/", visit_pdf),
                 path("health/", health),
                 path("api/insights/", insights),]

