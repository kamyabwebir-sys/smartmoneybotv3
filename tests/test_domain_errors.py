from dataclasses import FrozenInstanceError

import pytest

from smart_money.core.errors import DomainError


def test_valid_error_creation() -> None:
    error = DomainError(
        code="INVALID_STRUCTURE",
        message="Structure is invalid.",
        details={"field": "swing_high"},
    )

    assert error.code == "INVALID_STRUCTURE"
    assert error.message == "Structure is invalid."


@pytest.mark.parametrize("field_name", ["code", "message"])
@pytest.mark.parametrize("bad_value", ["", "   ", 123, None])
def test_rejects_invalid_required_string_fields(field_name: str, bad_value: object) -> None:
    values = {
        "code": "INVALID_STRUCTURE",
        "message": "Structure is invalid.",
    }
    values[field_name] = bad_value

    with pytest.raises(ValueError):
        DomainError(**values)


def test_defaults_details_to_empty_mapping() -> None:
    error = DomainError(code="INVALID_STRUCTURE", message="Structure is invalid.")

    assert dict(error.details) == {}


def test_details_are_defensively_copied() -> None:
    details = {"field": "swing_high"}

    error = DomainError(
        code="INVALID_STRUCTURE",
        message="Structure is invalid.",
        details=details,
    )

    details["field"] = "swing_low"

    assert dict(error.details) == {"field": "swing_high"}


def test_details_are_shallowly_immutable() -> None:
    error = DomainError(
        code="INVALID_STRUCTURE",
        message="Structure is invalid.",
        details={"field": "swing_high"},
    )

    with pytest.raises(TypeError):
        error.details["field"] = "swing_low"


def test_error_is_immutable() -> None:
    error = DomainError(code="INVALID_STRUCTURE", message="Structure is invalid.")

    with pytest.raises(FrozenInstanceError):
        error.code = "OTHER"


def test_to_dict_returns_plain_deterministic_dict() -> None:
    error = DomainError(
        code="INVALID_STRUCTURE",
        message="Structure is invalid.",
        details={"field": "swing_high"},
    )

    assert error.to_dict() == {
        "code": "INVALID_STRUCTURE",
        "message": "Structure is invalid.",
        "details": {"field": "swing_high"},
    }
    assert type(error.to_dict()["details"]) is dict
