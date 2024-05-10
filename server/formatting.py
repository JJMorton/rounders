from . import app

from datetime import datetime, UTC
from math import isnan

def format_date(timestamp: int) -> str:
    """Creates a date abbreviation to display to the user"""
    return (
        datetime.fromtimestamp(timestamp, UTC).strftime('%a %d %b')
        if timestamp != None and not isnan(timestamp) else 'TBC'
    )

def format_time(timestamp: int) -> str:
    """Creates a date-time abbreviation to display to the user"""
    return (
        datetime.fromtimestamp(timestamp, UTC).strftime('%H:%M')
        if timestamp != None and not isnan(timestamp) else ''
    )

def prepare_for_date_input(timestamp: int) -> str:
    """Puts the corresponding date into the correct format for a HTML input element"""
    if timestamp == None or isnan(timestamp):
        return ""
    d = datetime.fromtimestamp(timestamp, UTC)
    return d.strftime("%Y-%m-%d")

def prepare_for_time_input(timestamp: int) -> str:
    """Puts the corresponding time into the correct format for a HTML input element"""
    if timestamp == None or isnan(timestamp):
        return ""
    d = datetime.fromtimestamp(timestamp, UTC)
    return d.strftime("%H:%M")


# Allow for use in templates
app.jinja_env.globals.update(
    format_date=format_date,
    format_time=format_time,
    prepare_for_date_input=prepare_for_date_input,
    prepare_for_time_input=prepare_for_time_input,
)
