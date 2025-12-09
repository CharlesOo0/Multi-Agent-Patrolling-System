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
    instance_name:str ="no instance"
    instance_manager= InstanceManager()

    # Paramètres spécifiques aux algorithmes
    algo_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "Heuristic": {},
            "AntColony": {
                "evaporation_rate": 0.10,
                "alpha": 1.0,
                "beta": 2.0,
                "exploration_rate": 0.15,
                "tabu_length": 15,
            },
            "AntColonyLecture": {
                "evaporation_rate": 0.10,
                "alpha": 1.0,
                "beta": 2.0,
                "exploration_rate": 0.15,
                "tabu_length": 15,
            },
        }
    )

    # Mapping interne -> nom affiché (façade) pour l'UI
    algo_display_map: Dict[str, str] = field(
        default_factory=lambda: {
            "Heuristic": "Heuristic",
            "AntColony": "Ant Colony (Custom)",
            "AntColonyLecture": "Ant Colony (AI50 Version)",
        }
    )

    # Ordre d'affichage des algorithmes
    algo_order: list[str] = field(default_factory=lambda: ["Heuristic", "AntColony", "AntColonyLecture"])

    def internal_to_display(self, internal: str) -> str:
        return self.algo_display_map.get(internal, internal)

    def display_to_internal(self, display: str) -> str:
        for k, v in self.algo_display_map.items():
            if v == display:
                return k
        return display

    def algo_display_options(self) -> list[str]:
        return [self.algo_display_map.get(k, k) for k in self.algo_order]


# Global config instance
sim_config = SimConfig()
