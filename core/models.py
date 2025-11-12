from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PainEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pain_events")
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    pain_score = models.PositiveSmallIntegerField()      # 0–10
    fatigue = models.PositiveSmallIntegerField(default=0)  # 0–5
    body_sites = models.JSONField(default=list, blank=True)
    duration_min = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class HydrationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hydrations")
    date = models.DateField(db_index=True)
    volume_liters = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("user","date")

class LabResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="labs")
    observed_at = models.DateTimeField(db_index=True)
    analyte_code = models.CharField(max_length=16)      # HB, HBF, RETIC, LDH
    analyte_name = models.CharField(max_length=64)
    value = models.DecimalField(max_digits=8, decimal_places=3)
    unit = models.CharField(max_length=16)
    ref_low = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    ref_high = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
