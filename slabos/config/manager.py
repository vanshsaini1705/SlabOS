import json
from pathlib import Path

from project import generate_auth_pin


class ConfigManager:
    """Owns SlabOS persistent configuration."""

    CONFIG_FILE = Path("slabos_config.json")

    def save(self, config: dict) -> None:
        """Persist SlabOS configuration."""
        with self.CONFIG_FILE.open("w") as f:
            json.dump(config, f, indent=4)

    def load_or_create(self) -> dict:
        if self.CONFIG_FILE.exists():
            try:
                with self.CONFIG_FILE.open("r") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[!] Config read error ({exc}). Rebuilding.")

        config = {
            "master_pin": generate_auth_pin(4),
            "default_media_dir": "./media",
            "guest_pins": {},
        }

        with self.CONFIG_FILE.open("w") as f:
            json.dump(config, f, indent=4)

        return config
