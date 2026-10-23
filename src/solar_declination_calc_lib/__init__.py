"""Package entry point. Re-exports the public API."""

from .core import solar_declination, solar_declination_rad, day_of_year

__all__ = ["solar_declination", "solar_declination_rad", "day_of_year"]

__version__ = "1.0.0"
