"""Non-diagnostic safety notices for a user's symptom check-in history.

These rules do not diagnose a condition or determine an emergency. They only
surface clear, user-entered symptom patterns so the person can decide whether
to seek timely professional advice.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


SYMPTOM_RULES = (
    {
        "key": "chest_discomfort",
        "label": "Chest discomfort",
        "terms": ("chest pain", "chest pressure", "chest tightness"),
        "urgent": True,
    },
    {
        "key": "breathing_difficulty",
        "label": "Trouble breathing",
        "terms": ("trouble breathing", "shortness of breath", "breathlessness", "difficulty breathing"),
        "urgent": True,
    },
    {
        "key": "fainting",
        "label": "Fainting or blackout",
        "terms": ("fainted", "fainting", "passed out", "blackout"),
        "urgent": True,
    },
    {
        "key": "stroke_like",
        "label": "Stroke-like symptoms",
        "terms": ("face droop", "slurred speech", "one-sided weakness", "one sided weakness"),
        "urgent": True,
    },
    {
        "key": "palpitations",
        "label": "Palpitations",
        "terms": ("palpitations", "racing heart", "irregular heartbeat"),
        "urgent": False,
    },
    {
        "key": "dizziness",
        "label": "Dizziness",
        "terms": ("dizziness", "dizzy", "lightheaded"),
        "urgent": False,
    },
    {
        "key": "headache",
        "label": "Headache",
        "terms": ("headache", "head pain"),
        "urgent": False,
    },
    {
        "key": "leg_swelling",
        "label": "Leg or ankle swelling",
        "terms": ("leg swelling", "ankle swelling", "swollen ankles"),
        "urgent": False,
    },
)


def _as_naive_utc(value: Any) -> datetime | None:
    """Accept Mongo datetimes and ISO strings without mixing aware/naive time."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def build_symptom_alerts(checkins: Iterable[dict[str, Any]], now: datetime | None = None) -> list[dict[str, str]]:
    """Return plain-language notices for recent repeated symptom entries.

    A symptom category recorded on two or more separate check-ins in the past
    14 days gets a follow-up notice. Red-flag terms recorded in the last 24
    hours also get an immediate, conservative safety notice.
    """
    current_time = _as_naive_utc(now) or datetime.utcnow()
    repeat_cutoff = current_time - timedelta(days=14)
    urgent_cutoff = current_time - timedelta(days=1)
    repeated_entries: dict[str, set[int]] = defaultdict(set)
    recent_urgent: set[str] = set()

    for index, checkin in enumerate(checkins):
        recorded_at = _as_naive_utc(checkin.get("recorded_at"))
        if recorded_at is None:
            continue
        symptom_text = " ".join(str(item).lower().strip() for item in checkin.get("symptoms", []) if item)
        if not symptom_text:
            continue

        for rule in SYMPTOM_RULES:
            if not any(term in symptom_text for term in rule["terms"]):
                continue
            if recorded_at >= repeat_cutoff:
                repeated_entries[rule["key"]].add(index)
            if rule["urgent"] and recorded_at >= urgent_cutoff:
                recent_urgent.add(rule["key"])

    alerts: list[dict[str, str]] = []
    rules_by_key = {rule["key"]: rule for rule in SYMPTOM_RULES}
    for key in recent_urgent:
        rule = rules_by_key[key]
        alerts.append({
            "level": "urgent",
            "title": f"Safety note: {rule['label']} was logged recently",
            "message": (
                "If this symptom is new, severe, worsening, or happening now, seek urgent medical care "
                "instead of waiting for an app assessment."
            ),
        })

    for key, entry_ids in repeated_entries.items():
        if len(entry_ids) < 2:
            continue
        rule = rules_by_key[key]
        alerts.append({
            "level": "follow_up",
            "title": f"Repeated pattern: {rule['label']}",
            "message": (
                f"You recorded this on {len(entry_ids)} check-ins in the last 14 days. "
                "Consider discussing a persistent or worsening pattern with a healthcare professional."
            ),
        })

    return sorted(alerts, key=lambda alert: 0 if alert["level"] == "urgent" else 1)
