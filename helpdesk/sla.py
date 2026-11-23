
from datetime import datetime, timedelta, timezone


SLA_HOURS = {
    "Critical": 4,
    "High": 8,
    "Medium": 24,
    "Low": 72,
}


def utc_now():
    return datetime.now(timezone.utc)


def calculate_due_date(priority, created_at=None):
    created_at = created_at or utc_now()

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    hours = SLA_HOURS.get(priority, 24)

    return (
        created_at + timedelta(hours=hours)
    ).isoformat()


def parse_datetime(value):
    if not value:
        return None

    try:
        result = datetime.fromisoformat(value)

        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)

        return result
    except (ValueError, TypeError):
        return None


def is_overdue(ticket):
    if ticket["status"] in ("Resolved", "Closed"):
        return False

    due = parse_datetime(ticket["due_at"])

    return bool(due and utc_now() > due)


def time_left(ticket):
    due = parse_datetime(ticket["due_at"])

    if not due:
        return "No deadline"

    if ticket["status"] in ("Resolved", "Closed"):
        return "Completed"

    difference = due - utc_now()

    if difference.total_seconds() <= 0:
        return "Overdue"

    hours = int(difference.total_seconds() // 3600)
    minutes = int((difference.total_seconds() % 3600) // 60)

    if hours >= 24:
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}d {remaining_hours}h remaining"

    return f"{hours}h {minutes}m remaining"
