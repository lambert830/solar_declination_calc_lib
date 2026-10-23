"""Core calculation module for solar declination.

This module provides a self-contained, zero-dependency implementation of
the simplified Cooper equation for solar declination.  The formula used
here is the widely-cited approximation

    δ = 23.45° · sin(2π · (284 + N) / 365)

where N is the day-of-year (1 = Jan 1).  The equation ignores small
year-to-year variations in the vernal equinox date, so expect ±0.2°
error vs. high-precision ephemerides.  For solar-geometry work at
sub-degree accuracy (typical for irradiance, panel-tilt, and daylight
estimation) this trade-off is acceptable and keeps the library free of
tables or external data.

All functions are pure: given a (year, month, day) triple they return a
deterministic value with no clock dependency, so they can be unit-tested
without mocking time.
"""

import math

# Earth's obliquity (axial tilt) used by Cooper's approximation.  Modern
# measurements give ≈ 23.44°; 23.45° is retained here because it is the
# value embedded in the original Cooper (1969) formula, which this
# module deliberately follows for reproducibility.
_OBLIQUITY_DEG = 23.45

# Conversion factor — kept as a named constant so the intent is obvious.
_DEG_PER_RAD = 180.0 / math.pi


def _is_leap(year: int) -> bool:
    """Return True if *year* is a leap year under the proleptic Gregorian calendar.

    We use the proleptic Gregorian calendar (i.e. the rules applied to all
    years, including those before 1582) because Python's `datetime` does the
    same.  This gives a single, predictable rule and avoids needing a
    calendar-reform cut-off.
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    """Return the number of days in *month* of *year*.

    Raises ValueError for month outside 1..12, so callers can rely on a
    single error path for bad month input.
    """
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12, got %r" % (month,))

    if month == 2:
        return 29 if _is_leap(year) else 28

    # April, June, September, November have 30 days; the rest have 31.
    if month in (4, 6, 9, 11):
        return 30
    return 31


def day_of_year(year: int, month: int, day: int) -> int:
    """Compute the 1-based day-of-year for a Gregorian date.

    Parameters
    ----------
    year : int
        Any integer year in the proleptic Gregorian calendar.
    month : int
        Month, 1..12.
    day : int
        Day of month, 1..days-in-month.

    Returns
    -------
    int
        1 for Jan 1, 365 or 366 for Dec 31.

    Raises
    ------
    ValueError
        If month or day is out of range for the given year.

    Rationale
    --------
    We do not use `datetime.date.timetuple().tm_yday` because the project
    requires zero third-party deps *and* avoids any implicit dependency on
    `datetime`, which some embedded Python distributions omit.  Implementing
    the calendar arithmetic directly keeps the import surface to `math` only.
    """
    if not isinstance(year, int) or not isinstance(month, int) or not isinstance(day, int):
        raise TypeError("year, month, and day must all be integers")

    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError(
            "day %r is out of range for year=%d month=%d (1..%d)"
            % (day, year, month, dim)
        )

    # Cumulative days from Jan 1 to the start of each month (non-leap).
    # For leap years February adds one day, which is handled by adding
    # `_is_leap(year)` when month > 2 below.
    cum = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    return cum[month - 1] + day + (1 if month > 2 and _is_leap(year) else 0)


def solar_declination_rad(year: int, month: int, day: int) -> float:
    """Return solar declination in radians for a Gregorian date.

    Uses Cooper's approximation:

        δ = 23.45° · sin(2π · (284 + N) / 365)

    where N is the day-of-year (1-based).  See module docstring for the
    accuracy discussion.

    Parameters
    ----------
    year, month, day : int
        Gregorian date components.  Validated by `day_of_year`.

    Returns
    -------
    float
        Declination in radians, in the range [-23.45°, +23.45°].
    """
    n = day_of_year(year, month, day)
    return math.radians(_OBLIQUITY_DEG) * math.sin(
        2.0 * math.pi * (284 + n) / 365.0
    )


def solar_declination(year: int, month: int, day: int) -> float:
    """Return solar declination in degrees for a Gregorian date.

    Thin wrapper around `solar_declination_rad` that converts to degrees.
    Kept as a separate public function so callers who work in degrees
    (the more common unit for solar-position tables) do not need to
    import `math` themselves.

    Returns
    -------
    float
        Declination in degrees, in the range [-23.45, +23.45].
    """
    return solar_declination_rad(year, month, day) * _DEG_PER_RAD
