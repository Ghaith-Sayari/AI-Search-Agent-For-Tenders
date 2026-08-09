from models.opportunity import Opportunity
from datetime import date
from typing import Any


def validate_opportunity(opportunity: Opportunity) -> None:
    """Raises ValueError with all issues joined, or returns silently."""
    errors = opportunity.validate()
    if errors:
        raise ValueError(f"Invalid opportunity: {'; '.join(errors)}")


REQUIRED_EXTRACTION_FIELDS = [
    "sector",
    "sector_confidence",
    "country",
    "deadline",
    "key_requirements",
    "opportunity_type",
]

ALLOWED_SECTORS = {
    "IT Services",
    "Construction",
    "Healthcare",
    "Education",
    "Energy",
    "Transport",
    "Agriculture",
    "Finance",
    "Public Administration",
    "Other",
}


def validate_extraction_result(data: Any) -> list[str]:
    """
    Validates extraction output against prompts/output_schema.md.
    Returns a list of missing/invalid field errors (empty list = valid).
    """
    if not isinstance(data, dict):
        return ["extraction result must be a dictionary"]

    errors: list[str] = []

    missing = [f for f in REQUIRED_EXTRACTION_FIELDS if f not in data]
    if missing:
        errors.extend([f"missing field: {f}" for f in missing])
        return errors

    nullable_string_fields = ["sector", "country", "deadline", "opportunity_type"]
    for field in nullable_string_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"field '{field}' must be string or null")

    sector = data.get("sector")
    if isinstance(sector, str) and sector not in ALLOWED_SECTORS:
        errors.append(
            "field 'sector' must be one of: "
            + ", ".join(sorted(ALLOWED_SECTORS))
            + " (or null)"
        )

    sector_confidence = data.get("sector_confidence")
    if sector_confidence is not None:
        if not isinstance(sector_confidence, (int, float)):
            errors.append("field 'sector_confidence' must be a number between 0 and 1")
        elif not (0.0 <= float(sector_confidence) <= 1.0):
            errors.append("field 'sector_confidence' must be between 0 and 1")

    deadline = data.get("deadline")
    if isinstance(deadline, str):
        try:
            # Enforce semantic ISO date validity (YYYY-MM-DD + real calendar date)
            date.fromisoformat(deadline)
        except ValueError:
            errors.append("field 'deadline' must be a valid ISO date (YYYY-MM-DD) or null")

    key_requirements = data.get("key_requirements")
    if not isinstance(key_requirements, list):
        errors.append("field 'key_requirements' must be a list")
    elif not all(isinstance(item, str) for item in key_requirements):
        errors.append("field 'key_requirements' must contain only strings")

    return errors
