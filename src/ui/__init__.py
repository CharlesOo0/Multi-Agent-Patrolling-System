from .routes.base import Page, Router
from .routes.Home.home import HomePage
from .routes.Simulation.simulation import SimPage
from .routes.Statistics.statistics import StatsPage
from .routes.Settings.settings import SettingsPage
from .routes.MapEditor.MapEditor import MapEditorPage

__all__ = [
    "Page",
    "Router",
    "HomePage",
    "SimPage",
    "SettingsPage",
    "StatsPage",
    "MapEditorPage"
]
