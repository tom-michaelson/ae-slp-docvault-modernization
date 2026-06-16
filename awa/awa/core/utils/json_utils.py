import ast
import json


class JsonUtils:
    @staticmethod
    def parse_json(json_str: str) -> dict:
        result: dict | None = None
        try:
            result = json.loads(json_str)
        except json.decoder.JSONDecodeError:
            # Try parsing with single quotes (to support Windows edge cases)
            if "'" in json_str:
                result = ast.literal_eval(json_str)
            else:
                raise
        return result
