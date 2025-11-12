import math
from datetime import date, timedelta
from django.db.models import Avg, Count
from ..models import PainEvent, HydrationLog

def compute_daily_risk(user, d: date):
    d14 = d - timedelta(days=14)
    d2 = d - timedelta(days=2)

    baseline_pain_days = (
        PainEvent.objects.filter(user=user, occurred_at__date__gte=d14, occurred_at__date__lt=d)
        .values("occurred_at__date").annotate(n=Count("id")).count()
    )
    recent_pain_days = (
        PainEvent.objects.filter(user=user, occurred_at__date__gte=d2, occurred_at__date__lte=d)
        .values("occurred_at__date").annotate(n=Count("id")).count()
    )
    baseline_fatigue = list(PainEvent.objects.filter(
        user=user, occurred_at__date__gte=d14, occurred_at__date__lt=d
    ).values_list("fatigue", flat=True))
    todays_fatigue = (
        PainEvent.objects.filter(user=user, occurred_at__date=d).aggregate(avg=Avg("fatigue"))["avg"] or 0.0
    )
    baseline_hyd = list(HydrationLog.objects.filter(
        user=user, date__gte=d14, date__lt=d
    ).values_list("volume_liters", flat=True))
    todays_hyd = (
        HydrationLog.objects.filter(user=user, date=d).values_list("volume_liters", flat=True).first() or 0.0
    )

    def z(recent, baseline, adverse="high"):
        if not baseline:
            return 0.0
        mean = sum(float(x) for x in baseline) / len(baseline)
        var = sum((float(x) - mean) ** 2 for x in baseline) / max(1, len(baseline))
        sd = max(0.1, var ** 0.5)
        val = (float(recent) - mean) / sd
        return val if adverse == "high" else -val

    feats = {
        "pain_freq_z": z(recent_pain_days, [1]*max(1, baseline_pain_days), "high"),
        "fatigue_z": z(todays_fatigue, baseline_fatigue or [0.0], "high"),
        "hydration_deficit_z": z(todays_hyd, baseline_hyd or [0.0], "low"),
    }
    w = {"pain_freq_z":1.2, "fatigue_z":0.8, "hydration_deficit_z":1.0}
    raw = sum(w[k]*feats[k] for k in feats)
    score = int(round(100/(1+math.exp(-raw))))
    level = "low" if score < 40 else "moderate" if score < 70 else "high"
    explain = {k: round(v,2) for k,v in sorted(feats.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]}
    return score, level, explain
