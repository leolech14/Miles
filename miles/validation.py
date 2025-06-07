import yaml
import jsonschema

SOURCES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "name": {"type": "string"},
        },
        "required": ["url", "name"],
    },
}

def validate_sources_yaml(path="sources.yaml"):
    with open(path) as f:
        data = yaml.safe_load(f)
    jsonschema.validate(data, SOURCES_SCHEMA)