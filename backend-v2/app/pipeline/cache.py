import json
from pathlib import Path
from typing import Any


class ProductCache:
    def __init__(self, cache_directory: Path) -> None:
        self.cache_directory = cache_directory

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _path(self, key: str) -> Path:
        return self.cache_directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:

        path = self._path(key)

        if not path.exists():
            return None

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (OSError, json.JSONDecodeError):
            return None

        if not isinstance(data, dict):
            return None

        return data

    def set(
        self,
        key: str,
        data: dict[str, Any],
    ) -> None:

        path = self._path(key)

        temporary_path = path.with_suffix(".tmp")

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_path.replace(path)

    def contains(self, key: str) -> bool:

        return self._path(key).exists()
