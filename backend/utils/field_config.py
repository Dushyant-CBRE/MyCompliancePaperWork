"""
Field Configuration Manager
───────────────────────────
Loads and provides access to the field extraction configuration from YAML.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from backend.config import get_settings

logger = logging.getLogger(__name__)


class FieldConfig:
    """Represents a single field configuration."""

    def __init__(self, config_dict: dict):
        self.name: str = config_dict.get("name", "")
        self.type: str = config_dict.get("type", "string")
        self.required: bool = config_dict.get("required", False)
        self.description: str = config_dict.get("description", "")
        self.extraction_prompt: str = config_dict.get("extraction_prompt", "")
        self.examples: list[str] = config_dict.get("examples", [])
        self.validation_rules: dict = config_dict.get("validation_rules", {})
        self.fallback_value: Any = config_dict.get("fallback_value", None)
        self.confidence_field: bool = config_dict.get("confidence_field", False)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "examples": self.examples,
            "validation_rules": self.validation_rules,
            "fallback_value": self.fallback_value,
        }


class ExtractionConfigManager:
    """Manages field extraction configuration from YAML."""

    def __init__(self, config_path: str):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to field_extraction_config.yaml (relative to backend folder)
        """
        if yaml is None:
            raise ImportError("PyYAML not installed. Run: pip install pyyaml")

        # Resolve path relative to backend folder
        backend_folder = Path(__file__).parent.parent
        full_path = backend_folder / config_path

        if not full_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

        logger.info(f"Loaded field extraction config from {full_path}")
        self._fields_by_name = self._index_fields()

    def _index_fields(self) -> dict[str, FieldConfig]:
        """Index all fields by name for quick lookup."""
        fields = {}
        doc_types = self._config.get("document_types", {})

        # Extract fields from default document type or first available
        for doc_type_name, doc_type_config in doc_types.items():
            doc_fields = doc_type_config.get("fields", [])
            for field_dict in doc_fields:
                fc = FieldConfig(field_dict)
                fields[fc.name] = fc

        logger.info(f"Indexed {len(fields)} fields from configuration")
        return fields

    def get_field(self, field_name: str) -> Optional[FieldConfig]:
        """Get field configuration by name."""
        return self._fields_by_name.get(field_name)

    def get_all_fields(self) -> list[FieldConfig]:
        """Get all configured fields."""
        return list(self._fields_by_name.values())

    def get_required_fields(self) -> list[FieldConfig]:
        """Get only required fields."""
        return [f for f in self._fields_by_name.values() if f.required]

    def get_optional_fields(self) -> list[FieldConfig]:
        """Get only optional fields."""
        return [f for f in self._fields_by_name.values() if not f.required]

    def get_extraction_rules(self) -> dict:
        """Get compliance classification and remedial detection rules."""
        return {
            "compliance_classification": self._config.get("compliance_classification", {}),
            "remedial_detection": self._config.get("remedial_detection", {}),
        }

    def get_extraction_settings(self) -> dict:
        """Get global extraction settings."""
        return self._config.get("extraction_settings", {})


@lru_cache(maxsize=1)
def get_field_config_manager() -> ExtractionConfigManager:
    """Get or create the field configuration manager (cached singleton)."""
    settings = get_settings()
    return ExtractionConfigManager(settings.field_config_path)


def generate_extraction_prompt(field: FieldConfig) -> str:
    """Generate a field-specific extraction instruction."""
    prompt = f"**{field.name}** (Type: {field.type}, Required: {field.required})\n"
    prompt += f"{field.description}\n\n"
    prompt += f"Extraction instruction:\n{field.extraction_prompt}\n"

    if field.examples:
        prompt += "\nExamples:\n"
        for ex in field.examples:
            prompt += f"  - {ex}\n"

    return prompt


def generate_json_schema_from_config() -> dict:
    """Generate JSON schema for extraction output based on configuration."""
    manager = get_field_config_manager()
    schema = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for field in manager.get_all_fields():
        # Add the value field
        if field.type == "date":
            schema["properties"][field.name] = {
                "type": ["string", "null"],
                "description": field.description,
            }
        elif field.type == "array":
            schema["properties"][field.name] = {
                "type": "array",
                "items": {"type": "object"},
                "description": field.description,
            }
        else:
            schema["properties"][field.name] = {
                "type": ["string", "null"],
                "description": field.description,
            }

        # Add confidence field
        confidence_field_name = f"{field.name}_confidence"
        schema["properties"][confidence_field_name] = {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": f"Confidence score for {field.name}",
        }

        if field.required:
            schema["required"].append(field.name)
            schema["required"].append(confidence_field_name)

    # Add overall confidence
    schema["properties"]["overall_extraction_confidence"] = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "description": "Overall extraction confidence",
    }

    return schema
