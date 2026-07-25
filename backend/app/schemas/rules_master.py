from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RuleMasterOut(BaseModel):
    id: UUID
    rule_code: str
    rule_name: str
    description: str | None
    default_score: int
    is_active: bool
    config_schema: dict
    rule_content_version: int = 1

    model_config = {"from_attributes": True}


class RuleMasterUpdate(BaseModel):
    rule_name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    default_score: int | None = Field(None, ge=1, le=100)
    is_active: bool | None = None
    config_schema: dict | None = None

    @field_validator("config_schema")
    @classmethod
    def validate_config(cls, value: dict | None) -> dict | None:
        if value is None:
            return None
        return value


def validate_rule_config(rule_code: str, config: dict) -> dict:
    """Normalize and validate config_schema for a given rule code."""
    code = rule_code.upper()
    cleaned: dict = {}

    if code == "LARGE_VALUE":
        if "threshold" in config:
            raw = config["threshold"]
            if raw is None or raw == "":
                cleaned["threshold"] = None
            else:
                threshold = float(raw)
                if threshold <= 0:
                    raise ValueError("LARGE_VALUE threshold must be greater than zero.")
                cleaned["threshold"] = threshold

    elif code == "YEAR_END":
        if "days_before" in config:
            days = int(config["days_before"])
            if days < 1 or days > 30:
                raise ValueError("YEAR_END days_before must be between 1 and 30.")
            cleaned["days_before"] = days

    elif code == "ROUND_AMOUNT":
        if "suffixes" in config:
            suffixes = config["suffixes"]
            if not isinstance(suffixes, list) or not suffixes:
                raise ValueError("ROUND_AMOUNT suffixes must be a non-empty list.")
            parsed = [int(s) for s in suffixes]
            if any(s <= 0 for s in parsed):
                raise ValueError("ROUND_AMOUNT suffixes must be positive integers.")
            cleaned["suffixes"] = parsed

    elif code == "WEEKEND":
        if "weekdays" in config:
            weekdays = config["weekdays"]
            if not isinstance(weekdays, list) or not weekdays:
                raise ValueError("WEEKEND weekdays must be a non-empty list.")
            parsed = [int(d) for d in weekdays]
            if any(d < 0 or d > 6 for d in parsed):
                raise ValueError("WEEKEND weekdays must be between 0 (Mon) and 6 (Sun).")
            cleaned["weekdays"] = parsed

    elif code in ("SUSPENSE_ACCOUNT", "MANUAL_JOURNAL"):
        if "keywords" in config:
            keywords = config["keywords"]
            if not isinstance(keywords, list) or not keywords:
                raise ValueError(f"{code} keywords must be a non-empty list.")
            parsed = [str(k).strip().lower() for k in keywords if str(k).strip()]
            if not parsed:
                raise ValueError(f"{code} keywords must contain at least one value.")
            cleaned["keywords"] = parsed

    elif code == "UNUSUAL_POSTING":
        if "std_multiplier" in config:
            mult = float(config["std_multiplier"])
            if mult <= 0:
                raise ValueError("UNUSUAL_POSTING std_multiplier must be greater than zero.")
            cleaned["std_multiplier"] = mult
        if "min_count" in config:
            min_count = int(config["min_count"])
            if min_count < 1:
                raise ValueError("UNUSUAL_POSTING min_count must be at least 1.")
            cleaned["min_count"] = min_count

    else:
        raise ValueError(f"Unknown rule code: {rule_code}")

    return cleaned
