from rest_framework import serializers
from .models import PainEvent, HydrationLog, LabResult

class PainEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PainEvent
        fields = "__all__"
        read_only_fields = ("user","created_at")

class HydrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HydrationLog
        fields = "__all__"
        read_only_fields = ("user","created_at")

class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = "__all__"
        read_only_fields = ("user","created_at")
