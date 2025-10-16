from .routes.base import Page, Router
from .routes.Home.home import HomePage
from .routes.Simulation.simulation import SimPage
from .routes.Settings.settings import SettingsPage

__all__ = [
    "Page",
    "Router",
    "HomePage",
    "SimPage",
    "SettingsPage",
]
