from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PainEvent, HydrationLog, LabResult
from .serializers import PainEventSerializer, HydrationLogSerializer, LabResultSerializer


# must come first
class BaseOwnedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class PainEventViewSet(BaseOwnedViewSet):
    queryset = PainEvent.objects.all().order_by("-occurred_at")
    serializer_class = PainEventSerializer


class HydrationLogViewSet(BaseOwnedViewSet):
    queryset = HydrationLog.objects.all().order_by("-date")
    serializer_class = HydrationLogSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        obj, _created = HydrationLog.objects.update_or_create(
            user=request.user, date=data["date"],
            defaults={"volume_liters": data["volume_liters"]}
        )
        ser = self.get_serializer(obj)
        return Response(ser.data, status=status.HTTP_200_OK)


class LabResultViewSet(BaseOwnedViewSet):
    queryset = LabResult.objects.all().order_by("-observed_at")
    serializer_class = LabResultSerializer

from datetime import date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services.risk import compute_daily_risk

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def risk_today(request):
    d = date.fromisoformat(request.query_params.get("date")) if "date" in request.query_params else date.today()
    score, level, explain = compute_daily_risk(request.user, d)
    return Response({"date": str(d), "score": score, "level": level, "explain": explain})
