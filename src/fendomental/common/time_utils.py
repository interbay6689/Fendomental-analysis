import datetime


def monday_of_week(d: datetime.date) -> datetime.date:
    """The Monday of the ISO week containing d — used as economic_events/earnings_events.week_of."""
    return d - datetime.timedelta(days=d.weekday())
