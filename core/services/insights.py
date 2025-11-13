from datetime import date, timedelta
from statistics import mean
from django.db.models import Avg
from ..models import PainEvent, HydrationLog, LabResult

def hydration_vs_pain(user, days=28):
    end = date.today()
    start = end - timedelta(days=days)
    # merge by date
    pains = (PainEvent.objects.filter(user=user, occurred_at__date__gte=start, occurred_at__date__lte=end)
             .values("occurred_at__date").annotate(avg=Avg("pain_score")))
    hyds =  (HydrationLog.objects.filter(user=user, date__gte=start, date__lte=end)
             .values("date","volume_liters"))

    pain_by_day = {p["occurred_at__date"]: float(p["avg"]) for p in pains}
    hyd_by_day  = {h["date"]: float(h["volume_liters"]) for h in hyds}
    common_days = sorted(set(pain_by_day) & set(hyd_by_day))
    if len(common_days) < 5:
        return {"type":"hydration_pain","text":"Not enough overlapping days yet.","strength":"weak"}

    xs = [hyd_by_day[d] for d in common_days]
    ys = [pain_by_day[d] for d in common_days]
    # simple Pearson r
    xbar, ybar = mean(xs), mean(ys)
    num = sum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))
    den = (sum((x-xbar)**2 for x in xs)*sum((y-ybar)**2 for y in ys))**0.5 or 1.0
    r = num/den
    strength = "strong" if abs(r)>=0.6 else "moderate" if abs(r)>=0.3 else "weak"
    direction = "less" if r < 0 else "more"
    text = f"On higher-hydration days you reported {direction} pain (r={r:.2f}, {len(common_days)} days)."
    return {"type":"hydration_pain","text":text,"strength":strength}

def lab_drift_flags(user, codes=("HB","LDH","BILIRUBIN","RETIC")):
    flags = []
    for code in codes:
        vals = list(LabResult.objects.filter(user=user, analyte_code=code)
                    .order_by("-observed_at").values_list("value", flat=True)[:12])
        if len(vals) < 3:
            continue
        recent = float(vals[0]); base = [float(v) for v in vals[1:]]
        m = sum(base)/len(base)
        sd = (sum((v-m)**2 for v in base)/len(base))**0.5 or 0.1
        z = (recent - m)/sd
        if abs(z) >= 1.0:
            direction = "↓" if z < 0 else "↑"
            flags.append({"code":code, "z":round(z,2), "text": f"{code} {direction} vs baseline"})
    return {"type":"lab_drift","items":flags[:3]}
