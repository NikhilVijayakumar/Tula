import json
import os
from typing import Any, Dict, Union, List


class JsonUtils:

    @staticmethod
    def load_json_from_file(file_path: str) -> Union[Dict[str, Any], List[Any], None]:
        """Loads and parses a JSON file."""
        if not file_path: return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"  -> ❌ Error: The file at '{file_path}' was not found.")
        except json.JSONDecodeError:
            print(f"  -> ❌ Error: The file at '{file_path}' contains invalid JSON.")
        return None

    @staticmethod
    def save_json_to_file(data: Union[Dict, List], file_path: str) -> bool:
        """Saves a Python dictionary or list to a JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  -> ✅ Successfully saved JSON data to: {file_path}")
            return True
        except (OSError, TypeError) as e:
            print(f"  -> ❌ Error saving JSON file to '{file_path}': {e}")
            return False

    @staticmethod
    def _load_json_from_directory(directory_path: str) -> List[Dict[str, Any]]:
        """Scans a directory for .json files and loads them."""
        all_json_data = []
        if not os.path.isdir(directory_path):
            print(f"  -> ❌ Error: Directory '{directory_path}' not found.")
            return all_json_data

        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_json_data.append(json.load(f))
                except Exception as e:
                    print(f"    -> ⚠️ Could not parse '{filename}': {e}")
        return all_json_data