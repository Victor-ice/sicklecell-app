import math
from statistics import median
from datetime import date, timedelta
from django.db.models import Avg, Count
from ..models import PainEvent, HydrationLog, LabResult

LAB_WEIGHTS = {
    "HB": 0.8,          # lower is worse
    "HCT": 0.5,         # lower is worse
    "HBF": 0.6,         # higher is better
    "RETIC": 0.5,       # higher suggests hemolysis compensation
    "LDH": 0.8,         # higher is worse
    "BILIRUBIN": 0.6,   # higher is worse
    "CREATININE": 0.7,  # higher is worse
    "BUN": 0.4,         # higher can be dehydration/renal
    "WBC": 0.4,         # infection/inflammation
    "PLT": 0.3,         # context only
}

# direction: +1 if higher risk when higher, -1 if higher risk when lower
LAB_DIRECTION = {
    "HB": -1, "HCT": -1, "HBF": -1,
    "RETIC": +1, "LDH": +1, "BILIRUBIN": +1,
    "CREATININE": +1, "BUN": +1,
    "WBC": +1, "PLT": +1,
}

def _safe_sd(values):
    if len(values) < 2: return 0.1
    m = sum(values)/len(values)
    var = sum((v-m)**2 for v in values)/len(values)
    return max(0.1, var**0.5)

def _z(recent, baseline, adverse_dir=+1):
    if not baseline: return 0.0
    m = sum(baseline)/len(baseline)
    sd = _safe_sd(baseline)
    z = (recent - m)/sd
    return adverse_dir * z

def _last_value(vals):
    return vals[0] if vals else None

def compute_daily_risk(user, d: date):
    d14 = d - timedelta(days=14)
    d2  = d - timedelta(days=2)

    # symptoms/hydration
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
    today_fatigue = (
        PainEvent.objects.filter(user=user, occurred_at__date=d).aggregate(avg=Avg("fatigue"))["avg"] or 0.0
    )
    baseline_hyd = list(HydrationLog.objects.filter(
        user=user, date__gte=d14, date__lt=d
    ).values_list("volume_liters", flat=True))
    today_hyd = (
        HydrationLog.objects.filter(user=user, date=d).values_list("volume_liters", flat=True).first() or 0.0
    )

    feats = {
        "pain_freq_z": _z(recent_pain_days, [1]*max(1, baseline_pain_days), +1),
        "fatigue_z":   _z(float(today_fatigue), [float(x) for x in baseline_fatigue] or [0.0], +1),
        "hydration_deficit_z": _z(float(today_hyd), [float(x) for x in baseline_hyd] or [0.0], -1),
    }

    # labs: compare most recent value to 90-day median baseline
    d90 = d - timedelta(days=90)
    for code, w in LAB_WEIGHTS.items():
        qs = (LabResult.objects.filter(user=user, analyte_code=code, observed_at__date__lte=d)
              .order_by("-observed_at").values_list("value", flat=True))
        recent = _last_value([float(v) for v in qs[:1]])
        base_vals = [float(v) for v in qs[1:13]]  # up to 12 prior values
        if recent is not None and base_vals:
            m = median(base_vals)
            sd = _safe_sd(base_vals)
            z = (recent - m)/sd
            feats[f"{code}_z"] = LAB_DIRECTION[code] * z * w

    raw = sum(feats.values())
    score = int(round(100/(1+math.exp(-raw))))
    level = "low" if score < 40 else "moderate" if score < 70 else "high"
    explain = {k: round(v,2) for k,v in sorted(feats.items(), key=lambda kv: abs(kv[1]), reverse=True)[:4]}
    return score, level, explain
