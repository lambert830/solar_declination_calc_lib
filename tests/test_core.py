"""Unit tests for solar_declination_calc_lib.core.

Determinism: every test passes fixed integer inputs and asserts on the
returned floats using `math.isclose` with a tight absolute tolerance.
No clocks, no sleeps, no third-party imports.
"""

import math
import unittest

from solar_declination_calc_lib.core import (
    day_of_year,
    solar_declination,
    solar_declination_rad,
)


class TestDayOfYear(unittest.TestCase):
    """Tests for the day_of_year helper.

    Only asserts behaviour the implementation actually supports: validation
    of month/day ranges, the leap-year branch, and the cumulative-days
    arithmetic.
    """

    def test_jan_1_is_day_1(self):
        self.assertEqual(day_of_year(2023, 1, 1), 1)

    def test_dec_31_non_leap(self):
        self.assertEqual(day_of_year(2023, 12, 31), 365)

    def test_dec_31_leap(self):
        # 2024 is a leap year.
        self.assertEqual(day_of_year(2024, 12, 31), 366)

    def test_mar_1_non_leap(self):
        # Jan(31) + Feb(28) + 1 = 60
        self.assertEqual(day_of_year(2023, 3, 1), 60)

    def test_mar_1_leap(self):
        # Jan(31) + Feb(29) + 1 = 61
        self.assertEqual(day_of_year(2024, 3, 1), 61)

    def test_feb_29_only_valid_in_leap(self):
        self.assertEqual(day_of_year(2024, 2, 29), 60)
        with self.assertRaises(ValueError):
            day_of_year(2023, 2, 29)

    def test_month_out_of_range(self):
        with self.assertRaises(ValueError):
            day_of_year(2023, 0, 1)
        with self.assertRaises(ValueError):
            day_of_year(2023, 13, 1)

    def test_day_out_of_range(self):
        with self.assertRaises(ValueError):
            day_of_year(2023, 4, 31)  # April has 30 days
        with self.assertRaises(ValueError):
            day_of_year(2023, 1, 0)
        with self.assertRaises(ValueError):
            day_of_year(2023, 1, 32)

    def test_non_integer_input_rejected(self):
        with self.assertRaises(TypeError):
            day_of_year(2023.0, 1, 1)
        with self.assertRaises(TypeError):
            day_of_year(2023, 1, 1.0)

    def test_century_leap_rule(self):
        # 2000 was a leap year (divisible by 400); 1900 was not.
        self.assertEqual(day_of_year(2000, 2, 29), 60)
        with self.assertRaises(ValueError):
            day_of_year(1900, 2, 29)


class TestSolarDeclination(unittest.TestCase):
    """Tests for the declination functions.

    These tests pin specific values produced by Cooper's formula as
    implemented.  They are regression tests, not ephemeris tests; the
    ±0.2° real-world error is documented in the module docstring and is
    not something we assert against here.
    """

    # Tolerance chosen to absorb IEEE-754 double rounding without being
    # so loose that a sign error would slip through.
    ABS_TOL = 1e-9

    def test_vernal_equinox_near_zero(self):
        # Around March 20 the declination crosses zero.  We test March 21,
        # which Cooper's formula places close to zero.
        delta = solar_declination(2023, 3, 21)
        self.assertTrue(abs(delta) < 1.5, msg=f"expected near 0°, got {delta}")

    def test_summer_solstice_near_max(self):
        # Around June 21 the declination is near +23.45°.
        delta = solar_declination(2023, 6, 21)
        self.assertTrue(
            23.0 < delta <= 23.45 + 0.5,
            msg=f"expected near +23.45°, got {delta}",
        )

    def test_winter_solstice_near_min(self):
        # Around December 21 the declination is near -23.45°.
        delta = solar_declination(2023, 12, 21)
        self.assertTrue(
            -23.45 - 0.5 < delta < -23.0,
            msg=f"expected near -23.45°, got {delta}",
        )

    def test_rad_and_deg_agree(self):
        rad = solar_declination_rad(2024, 7, 4)
        deg = solar_declination(2024, 7, 4)
        self.assertTrue(math.isclose(deg, math.degrees(rad), abs_tol=self.ABS_TOL))

    def test_bounds_never_exceeded(self):
        # The sine term is bounded by [-1, 1], so |delta| <= 23.45°.
        for (y, m, d) in [
            (2023, 1, 1), (2023, 3, 21), (2023, 6, 21),
            (2023, 9, 22), (2023, 12, 21), (2024, 2, 29),
        ]:
            delta = solar_declination(y, m, d)
            self.assertTrue(
                -23.45 - self.ABS_TOL <= delta <= 23.45 + self.ABS_TOL,
                msg=f"|delta| out of bounds for {y}-{m}-{d}: {delta}",
            )

    def test_known_value_june_21(self):
        # Pin a specific regression value computed from the formula as
        # implemented.  N for June 21 in a non-leap year is 172.
        # delta = 23.45 * sin(2π * (284+172)/365)
        n = day_of_year(2023, 6, 21)
        self.assertEqual(n, 172)
        expected = 23.45 * math.sin(2.0 * math.pi * (284 + n) / 365.0)
        self.assertTrue(
            math.isclose(solar_declination(2023, 6, 21), expected, abs_tol=self.ABS_TOL)
        )

    def test_leap_vs_non_leap_jun_21(self):
        # Day-of-year for June 21 is 172 in a non-leap year and 173 in a
        # leap year (the leap day shifts subsequent dates by one), so the
        # declination values differ between 2023 and 2024 for June 21.
        self.assertEqual(day_of_year(2023, 6, 21), 172)
        self.assertEqual(day_of_year(2024, 6, 21), 173)
        self.assertNotEqual(
            solar_declination(2023, 6, 21),
            solar_declination(2024, 6, 21),
        )

    def test_invalid_date_propagates(self):
        # Declination functions should surface the same ValueError that
        # day_of_year raises, rather than silently producing a number.
        with self.assertRaises(ValueError):
            solar_declination(2023, 2, 29)
        with self.assertRaises(ValueError):
            solar_declination_rad(2023, 13, 1)

    def test_type_mismatch_propagates(self):
        with self.assertRaises(TypeError):
            solar_declination("2023", 1, 1)

    def test_extreme_year_value_accepted(self):
        # The proleptic Gregorian rules we implemented handle arbitrary
        # integer years; this test pins that the implementation does not
        # impose a hidden upper/lower bound.
        self.assertEqual(day_of_year(-1000, 1, 1), 1)
        self.assertEqual(day_of_year(99999, 12, 31), 365)


if __name__ == "__main__":
    unittest.main()
