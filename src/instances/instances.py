from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import json


@dataclass
class Instance:
    """Representation of a saved instance for the simulation.

    Attributes
    - name: Human-friendly name of the instance
    - id: Numeric identifier
    - nb_agent: Number of agents to spawn for this instance
    - position: List of (x, y) tuples for agent spawn positions
    - map_name: Name of the map this instance belongs to
    - idleness_growth: Growth rate of idleness for this instance
    - event_appearance_list: Optional list of (step to appear, position) tuples for event appearances
    """
    name: str
    id: int
    nb_agent: int
    position: List[Tuple[int, int]]
    map_name: str
    idleness_growth: float = 0.05
    event_appearance_list: Optional[Dict[int, Dict]] = None


class InstanceManager:
    """Manager for loading, querying and saving instance definitions.

    This class exposes a small, pythonic API instead of numerous trivial
    getters. Use `names(map_name=None)` to list instance names and `get(name)`
    to obtain the `Instance` dataclass. The manager loads a JSON file that is
    expected to live next to this module (``instances.json``). If the file is
    missing or malformed, the manager falls back to an empty list and avoids
    raising on import.
    """

    def __init__(self, instances_path: Optional[Path] = None) -> None:
        # Resolve default path relative to this file for portability
        default = Path(__file__).resolve().parent / "instances.json"
        self.instances_json: Path = Path(instances_path) if instances_path else default
        self.instances: List[Instance] = []
        self._load()

    def _load(self) -> None:
        """Load instances from the configured JSON file.

        The JSON is expected to be either a mapping containing the key
        "instance" (list) or a raw list of instances. Positions are
        converted to tuples for convenient usage.
        """
        if not self.instances_json.exists():
            # Missing file: keep an empty list but do not raise during import
            self.instances = []
            return

        try:
            with open(self.instances_json, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            # Malformed JSON: keep empty instances instead of raising
            self.instances = []
            return

        raw_list = []
        if isinstance(data, dict) and "instance" in data:
            raw_list = data.get("instance", [])
        elif isinstance(data, list):
            raw_list = data

        parsed: List[Instance] = []
        for item in raw_list:
            print(item)
            try:
                positions = [tuple(p) for p in item.get("position", [])]
                inst = Instance(
                    name=item.get("name", ""),
                    id=int(item.get("id", 0)),
                    nb_agent=int(item.get("nb_agent", 0)),
                    position=positions,
                    map_name=item.get("map_name", ""),
                    idleness_growth=float(item.get("idleness_growth", item.get("iddleness_growth", 0.05))),
                    event_appearance_list=item.get("event_appearance_list", None),
                )
                parsed.append(inst)
            except Exception:
                # Skip invalid items but continue loading others
                continue

        self.instances = parsed

    def save(self) -> None:
        """Persist current instances to the JSON file.

        The file is written with an explicit top-level key "instance" to keep
        compatibility with the original format.
        """
        payload = {"instance": [
            {
                "name": inst.name,
                "id": inst.id,
                "nb_agent": inst.nb_agent,
                "position": [list(p) for p in inst.position],
                "map_name": inst.map_name,
                "idleness_growth": inst.idleness_growth,
                "event_appearance_list": inst.event_appearance_list,
            }
            for inst in self.instances
        ]}

        # Ensure parent directory exists and write atomically
        try:
            self.instances_json.parent.mkdir(parents=True, exist_ok=True)
            with open(self.instances_json, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=4)
        except Exception:
            # Fail silently to avoid breaking UI code on save errors
            pass

    # --- Public, pythonic API ---
    def names(self, map_name: Optional[str] = None) -> List[str]:
        """Return a list of instance names filtered by `map_name`.

        Always returns a list that ends with the special value "no instance".
        """
        if map_name is None:
            result = [inst.name for inst in self.instances]
        else:
            result = [inst.name for inst in self.instances if inst.map_name == map_name]
        return result + ["no instance"]

    def get(self, name: str) -> Optional[Instance]:
        """Return the instance matching `name`, or ``None`` if not found."""
        return next((inst for inst in self.instances if inst.name == name), None)

    def add(self, instance: Instance) -> None:
        """Append a new instance and persist the change."""
        self.instances.append(instance)
        self.save()

    def __iter__(self):
        return iter(self.instances)

    def __len__(self) -> int:
        return len(self.instances)
