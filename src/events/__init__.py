"""Events package exposing CS:GO-like game events affecting idleness."""

from .events import EventType, Event, EventManager  # noqa: F401

__all__ = ["EventType", "Event", "EventManager"]
