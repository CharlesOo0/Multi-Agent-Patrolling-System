from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

import numpy as np


class MapLoader:
    """Load and save grid maps (0=free, 1=obstacle) from/to JSON files.

    JSON schema (flexible):
    {
      "name": "DUST2",               # optional
      "grid": [[0,1, ...], [...]],    # required: list of list of ints
      "rows": 28,                      # optional (informational)
      "cols": 26                       # optional (informational)
    }
    """

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent

    def _resolve_path(self, filename_or_name: Union[str, Path], extension : str) -> Path:
        p = Path(filename_or_name)
        if not p.suffix:
            # Accept a bare name like "DUST2" and append .json in base_dir
            p = self.base_dir / f"{p.name}.{extension}"
        elif not p.is_absolute():
            p = self.base_dir / p
        return p
    
    def load(self, filename_or_name: Union[str, Path]) -> np.ndarray:
        """Load a map from JSON and return it as a numpy int array of 0/1.

        Accepts either a filename (with or without .json) or a Path.
        """
        path = self._resolve_path(filename_or_name,"json")
        if not path.exists():
            raise FileNotFoundError(f"Map JSON not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        grid = data.get("grid")
        if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
            raise ValueError("Invalid JSON map: 'grid' must be a list of lists")

        arr = np.array(grid, dtype=int)
        # Normalize any non-zero value to 1 (obstacle), keep 0 as free
        arr = np.where(arr != 0, 1, 0)
        return arr

    def load_offset(self, filename_or_name: Union[str, Path]) -> np.ndarray:
        """Return the offset to display the map from JSON.

        Accepts either a filename (with or without .json) or a Path.
        """
        path = self._resolve_path(filename_or_name,"json")
        if not path.exists():
            raise FileNotFoundError(f"Map JSON not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        offset_x = data.get("map_offset_x")
        offset_y = data.get("map_offset_y")
        if offset_x == None or offset_y == None:
            raise ValueError("Invalid JSON : offset_y or offset_x not found")

        return offset_x,offset_y

    def load_png(self, filename_or_name: Union[str, Path]) -> Path:
        """Return the path of the background of the map.

        Accepts either a filename (with or without .json) or a Path.
        """
        path = self._resolve_path(filename_or_name,"png")
        if not path.exists():
            raise FileNotFoundError(f"Map JSON not found: {path}")
        return path

    def save(self, arr: np.ndarray, filename_or_name: Union[str, Path], *, name: Optional[str] = None, overwrite: bool = True) -> Path:
        """Save a numpy array as a JSON map file. Returns the written Path."""
        path = self._resolve_path(filename_or_name,"json")
        if path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")

        rows, cols = arr.shape
        payload = {
            "name": name or path.stem,
            "rows": int(rows),
            "cols": int(cols),
            "grid": arr.astype(int).tolist(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
