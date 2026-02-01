# config_utils/config_manager.py
from enum import Enum
from core.test_type import TestType
from config_utils.property_reader import PropertyReader
import os

"""
Config load order:
  1) config/qa.properties                     # base (committed)
  2) config/qa.local.properties (optional)    # local overlay (gitignored) — overrides base

Notes:
- qa.local.properties is optional and can be used for secrets; DO NOT COMMIT.
- Single qa.properties file is used for all configurations.
"""

class ConfigManager:
    """Load UI config from qa.properties with optional local overlay."""
    _loaded_configs = {}

    def __init__(self, module: TestType):
        self.module = module

        # Use qa.properties as the base configuration file
        base_path = os.path.join("config", "qa.properties")
        # Local/secret overlay (gitignored). Optional; overrides base if exists.
        local_path = os.path.join("config", "qa.local.properties")

        cache_key = (module.value, "qa")
        if cache_key not in ConfigManager._loaded_configs:
            if not os.path.exists(base_path):
                raise FileNotFoundError(f"Property file not found: {base_path}")

            base_reader = PropertyReader(base_path)
            merged = dict(getattr(base_reader, "properties", {}))

            # Optional local overlay (for secrets)
            if os.path.exists(local_path):
                local_reader = PropertyReader(local_path)
                merged.update(getattr(local_reader, "properties", {}))  # overlay on top

            class _DictReader:
                def __init__(self, data: dict):
                    self._d = data
                def get_property(self, key: str, default=None):
                    return self._d.get(key, default)

            ConfigManager._loaded_configs[cache_key] = _DictReader(merged)

        self.reader = ConfigManager._loaded_configs[cache_key]

    def get(self, key_enum: Enum):
        return self.reader.get_property(key_enum.value)