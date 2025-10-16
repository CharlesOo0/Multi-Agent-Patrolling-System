from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class SimConfig:
    """Configuration partagée pour la simulation.

    Note: Cette config est lue par `SimPage.on_enter` au lancement de la simulation.
    Modifiez-la depuis la page Settings.
    """

    map_name: str = "DUST2"
    algorithm: str = "Heuristic"  # "Heuristic" | "AntColony"
    num_agents: int = 4
    spawn_prob: float = 0.05

    # Paramètres spécifiques aux algorithmes
    algo_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "Heuristic": {},
            "AntColony": {
                "evaporation_rate": 0.10,
                "alpha": 1.0,
                "beta": 2.0,
            },
        }
    )


# Singleton simple utilisé par les pages
sim_config = SimConfig()
