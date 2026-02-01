import os

class PropertyReader:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Property file not found: {file_path}")
        self.file_path = file_path
        self.properties = self._load_properties()

    def _expand_value(self, value: str) -> str:
        # strip surrounding quotes if present
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # expand ${VAR}, $VAR and ~
        value = os.path.expandvars(value)
        value = os.path.expanduser(value)
        return value

    def _load_properties(self) -> dict:
        """Read property file and return as dictionary"""
        props = {}
        with open(self.file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key_value = line.split("=", 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        props[key.strip()] = self._expand_value(value.strip())
        return props

    def get_property(self, key: str, default=None):
        """Get a property value by key"""
        return self.properties.get(key, default)