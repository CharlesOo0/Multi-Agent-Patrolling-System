"""Events package exposing CS:GO-like game events affecting idleness."""

from .events import Event, EventManager  # noqa: F401

__all__ = ["Event", "EventManager"]
