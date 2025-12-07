from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any
from instances.instances import InstanceManager


@dataclass
class SimConfig:
    """Global simulation configuration accessible par les pages.

    Note: This config is read by `SimPage.on_enter` when starting the simulation.
    Modify it from the Settings page.
    """

    map_name: str = "DUST2"
    algorithm: str = "Heuristic"  # "Heuristic" | "AntColony"
    num_agents: int = 4
    spawn_prob: float = 0.05
    iddleness_growth: float = 0.05
    agent_instance_name:str ="no instance"
    event_instance_name:str ="no instance"
    instance_manager= InstanceManager()

    # Paramètres spécifiques aux algorithmes
    algo_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "Heuristic": {},
            "AntColony": {
                "evaporation_rate": 0.10,
                "alpha": 1.0,
                "beta": 2.0,
            },
            "AntColonyLecture": {
                "evaporation_rate": 0.10,
                "alpha": 1.0,
                "beta": 2.0,
            },
        }
    )


# Global config instance
sim_config = SimConfig()
