from typing import Dict, Any

import yaml


class YamlUtils:

    @staticmethod
    def yaml_safe_load(config_path: str) -> Dict[str, Any]:
        """Loads and validates the YAML configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Error: Configuration file not found at '{config_path}'")
            exit()
        except yaml.YAMLError as e:
            print(f"❌ Error: Could not parse YAML configuration file. Details: {e}")
            exit()