# solar_declination_calc_lib

`I(t) = I0 * cos(θ)`


A tiny, dependency-free Python library that calculates the solar declination angle for any day of the year.


## Installation

```bash
pip install solar_declination_calc_lib
```


## Usage

```python
from solar_declination_calc_lib import solar_declination, solar_declination_rad, day_of_year

# Solar declination on June 21st, 2024 (summer solstice in the northern hemisphere)
angle_deg = solar_declination(2024, 6, 21)
print(f"Declination: {angle_deg:.2f}°")
# Expected output: Declination: 23.45° (approx)

# You can also get the value in radians
angle_rad = solar_declination_rad(2024, 6, 21)

# And use the helper to find the day of the year for any date
n = day_of_year(2024, 3, 21)
print(f"March 21st is day {n} of the year")
# Expected output: March 21st is day 81 of the year
```


## Why This Library Exists

For many solar-energy and agricultural applications, you need the solar declination angle to compute the sun's elevation and azimuth. High-precision ephemerides can give this value to arcsecond accuracy, but they require large data tables or network calls.

This library provides a simple, closed-form approximation of the declination angle based on Cooper's formula. The trade-off is accuracy for simplicity and portability: the formula ignores small year-to-year variations in the vernal equinox date, leading to an expected error of approximately ±0.2° compared to high-precision sources.

For most practical engineering, architectural, and agricultural purposes, this level of accuracy is more than sufficient.


## An Awkward Edge: Leap Years

The most common stumbling block with declination calculators is the handling of leap years. Because the Cooper formula takes the day-of-year (N) as input, the same calendar date (e.g., June 21st) will have a different N value in a leap year versus a non-leap year only if the date falls after February 28th.

*Wait, let's clarify that:* Actually, for dates from January 1st to February 28th, the day-of-year N is the same in both leap and non-leap years. For dates from March 1st to December 31st, N is one greater in a leap year.

**How this library handles it:**

This library uses a proleptic Gregorian calendar to correctly compute the day-of-year for any given date, including proper handling of leap years (including the century rules, where years divisible by 100 are *not* leap years unless also divisible by 400).

As a result, the calculated declination angle will differ slightly between, for example, June 21st, 2023 (a non-leap year) and June 21st, 2024 (a leap year), because the underlying day-of-year value is different.

**Correction:** Please double-check the `test_leap_vs_non_leap_jun_21` test in `tests/test_core.py`. As noted in the test, the day-of-year for June 21st is actually 172 in *both* leap and non-leap years, because the extra day in a leap year (February 29th) has already been accounted for by the time you reach June. Therefore, the calculated declination angle for a specific month and day will be identical in leap and non-leap years for any date from March 1st onwards.

*So, the actual awkward edge is:* the formula itself is based on a 365-day cycle, but leap years have 366 days. This means the declination angle for December 31st in a leap year will be "shifted" relative to the solar cycle compared to a non-leap year. This is an inherent limitation of the Cooper formula and contributes to the ±0.2° error margin. The library does not attempt to correct for this, keeping the implementation transparent and aligned with the original formula.


## API

The library exports the following names:

- `day_of_year(year: int, month: int, day: int) -> int`
- `solar_declination_rad(year: int, month: int, day: int) -> float`
- `solar_declination(year: int, month: int, day: int) -> float`
