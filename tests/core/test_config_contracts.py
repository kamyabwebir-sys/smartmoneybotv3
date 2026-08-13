import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from smart_money.core.config import ConfigVersionLock, DeterministicConfig
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json

NAMESPACE = "deterministic_config"


def sample_payload() -> dict:
    return {
        "threshold": 10,
        "enabled": True,
        "label": "alpha",
    }


def sample_payload_json() -> str:
    return canonical_json(sample_payload())


def payload_digest(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def identity_payload(
    *,
    config_kind: str = "structure_rules",
    schema_version: str = "1.0.0",
    config_version: str = "2.1.0",
    payload_json: str | None = None,
) -> dict:
    if payload_json is None:
        payload_json = sample_payload_json()

    return {
        "config_kind": config_kind,
        "schema_version": schema_version,
        "config_version": config_version,
        "payload_digest": payload_digest(payload_json),
    }


def expected_config_id(
    *,
    config_kind: str = "structure_rules",
    schema_version: str = "1.0.0",
    config_version: str = "2.1.0",
    payload_json: str | None = None,
) -> str:
    return deterministic_id(
        NAMESPACE,
        identity_payload(
            config_kind=config_kind,
            schema_version=schema_version,
            config_version=config_version,
            payload_json=payload_json,
        ),
    )


def make_config(
    *,
    config_kind: str = "structure_rules",
    schema_version: str = "1.0.0",
    config_version: str = "2.1.0",
    payload_json: str | None = None,
    payload_digest_value: str | None = None,
    config_id: str | None = None,
) -> DeterministicConfig:
    if payload_json is None:
        payload_json = sample_payload_json()

    if payload_digest_value is None:
        payload_digest_value = payload_digest(payload_json)

    if config_id is None:
        config_id = expected_config_id(
            config_kind=config_kind,
            schema_version=schema_version,
            config_version=config_version,
            payload_json=payload_json,
        )

    return DeterministicConfig(
        config_kind=config_kind,
        schema_version=schema_version,
        config_version=config_version,
        payload_json=payload_json,
        payload_digest=payload_digest_value,
        config_id=config_id,
    )


# ---------------------------------------------------------------------------
# DeterministicConfig construction / identity
# ---------------------------------------------------------------------------


def test_deterministic_config_accepts_valid_canonical_config():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    config_id = expected_config_id(payload_json=payload_json)

    cfg = DeterministicConfig(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        payload_json=payload_json,
        payload_digest=digest,
        config_id=config_id,
    )

    assert cfg.config_kind == "structure_rules"
    assert cfg.schema_version == "1.0.0"
    assert cfg.config_version == "2.1.0"
    assert cfg.payload_json == payload_json
    assert cfg.payload_digest == digest
    assert cfg.config_id == config_id


def test_deterministic_config_id_matches_repo_deterministic_id():
    payload_json = sample_payload_json()
    expected = expected_config_id(payload_json=payload_json)

    cfg = make_config(payload_json=payload_json, config_id=expected)

    assert cfg.config_id == expected
    assert cfg.config_id.startswith("deterministic_config_")

    suffix = cfg.config_id.removeprefix("deterministic_config_")
    assert len(suffix) == 32
    assert suffix == suffix.lower()
    assert all(ch in "0123456789abcdef" for ch in suffix)


def test_deterministic_config_rejects_config_id_that_does_not_match_recomputed_value():
    payload_json = sample_payload_json()

    with pytest.raises(ValueError, match="config_id"):
        make_config(
            payload_json=payload_json,
            config_id="deterministic_config_00000000000000000000000000000000",
        )


def test_deterministic_config_rejects_payload_digest_that_does_not_match_recomputed_value():
    payload_json = sample_payload_json()
    wrong_digest = "0" * 64
    if wrong_digest == payload_digest(payload_json):
        wrong_digest = "1" * 64

    with pytest.raises(ValueError, match="payload_digest"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=wrong_digest,
            config_id=expected_config_id(payload_json=payload_json),
        )


# ---------------------------------------------------------------------------
# payload_json validation
# ---------------------------------------------------------------------------


def test_deterministic_config_rejects_non_canonical_payload_json_with_whitespace():
    payload_json = json.dumps(sample_payload(), sort_keys=True, indent=2)

    with pytest.raises(ValueError, match="canonical"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id=expected_config_id(payload_json=payload_json),
        )


def test_deterministic_config_rejects_non_canonical_payload_json_with_unsorted_keys():
    payload_json = '{"threshold":10,"enabled":true,"label":"alpha"}'

    with pytest.raises(ValueError, match="canonical"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id=expected_config_id(payload_json=payload_json),
        )


def test_deterministic_config_rejects_invalid_json_payload():
    payload_json = "{not-json"

    with pytest.raises(ValueError, match="payload_json"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id="deterministic_config_00000000000000000000000000000000",
        )


def test_deterministic_config_rejects_payload_json_array():
    payload_json = canonical_json([1, 2, 3])

    with pytest.raises(ValueError, match="object"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id="deterministic_config_00000000000000000000000000000000",
        )


@pytest.mark.parametrize("payload_json", ["true", "123", '"abc"', "null"])
def test_deterministic_config_rejects_payload_json_scalar(payload_json):
    with pytest.raises(ValueError, match="object"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id="deterministic_config_00000000000000000000000000000000",
        )


@pytest.mark.parametrize("payload_json", ["", " ", "\n"])
def test_deterministic_config_rejects_empty_payload_json(payload_json):
    with pytest.raises(ValueError, match="payload_json"):
        make_config(
            payload_json=payload_json,
            payload_digest_value=payload_digest(payload_json),
            config_id="deterministic_config_00000000000000000000000000000000",
        )


# ---------------------------------------------------------------------------
# version validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "version",
    [
        "0.0.0",
        "0.1.2",
        "1.0.0",
        "10.20.30",
    ],
)
def test_deterministic_config_accepts_valid_version_formats(version):
    payload_json = sample_payload_json()

    cfg = make_config(
        schema_version=version,
        config_version=version,
        payload_json=payload_json,
    )

    assert cfg.schema_version == version
    assert cfg.config_version == version


@pytest.mark.parametrize(
    "field_name,version",
    [
        ("schema_version", "01.0.0"),
        ("schema_version", "1.02.0"),
        ("schema_version", "1.0.003"),
        ("schema_version", "00.0.0"),
        ("config_version", "01.0.0"),
        ("config_version", "1.02.0"),
        ("config_version", "1.0.003"),
        ("config_version", "00.0.0"),
    ],
)
def test_deterministic_config_rejects_versions_with_leading_zero(field_name, version):
    kwargs = {
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = version

    with pytest.raises(ValueError, match=field_name):
        make_config(**kwargs)


@pytest.mark.parametrize(
    "field_name,version",
    [
        ("schema_version", "1"),
        ("schema_version", "1.0"),
        ("schema_version", "1.0.0.0"),
        ("schema_version", "v1.0.0"),
        ("schema_version", "1.0.0-alpha"),
        ("schema_version", "1.0.x"),
        ("schema_version", "-1.0.0"),
        ("schema_version", "1..0"),
        ("schema_version", ".1.0"),
        ("schema_version", "1.0."),
        ("config_version", "1"),
        ("config_version", "1.0"),
        ("config_version", "1.0.0.0"),
        ("config_version", "v1.0.0"),
        ("config_version", "1.0.0-alpha"),
        ("config_version", "1.0.x"),
        ("config_version", "-1.0.0"),
        ("config_version", "1..0"),
        ("config_version", ".1.0"),
        ("config_version", "1.0."),
    ],
)
def test_deterministic_config_rejects_malformed_versions(field_name, version):
    kwargs = {
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = version

    with pytest.raises(ValueError, match=field_name):
        make_config(**kwargs)


# ---------------------------------------------------------------------------
# required field type/value validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("config_kind", ["", " ", "\n"])
def test_deterministic_config_rejects_empty_config_kind(config_kind):
    with pytest.raises(ValueError, match="config_kind"):
        make_config(
            config_kind=config_kind,
            config_id="deterministic_config_00000000000000000000000000000000",
        )


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("config_kind", 123),
        ("schema_version", 123),
        ("config_version", 123),
        ("payload_json", {"x": 1}),
        ("payload_digest", 123),
        ("config_id", 123),
    ],
)
def test_deterministic_config_rejects_non_string_fields_with_type_error(
    field_name,
    bad_value,
):
    payload_json = sample_payload_json()

    kwargs = {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
        "payload_json": payload_json,
        "payload_digest": payload_digest(payload_json),
        "config_id": expected_config_id(payload_json=payload_json),
    }
    kwargs[field_name] = bad_value

    with pytest.raises(TypeError, match=field_name):
        DeterministicConfig(**kwargs)


def test_deterministic_config_is_immutable():
    cfg = make_config()

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "9.9.9"


# ---------------------------------------------------------------------------
# ConfigVersionLock construction / validation
# ---------------------------------------------------------------------------


def test_config_version_lock_accepts_version_only_lock():
    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.config_kind == "structure_rules"
    assert lock.schema_version == "1.0.0"
    assert lock.config_version == "2.1.0"
    assert lock.required_payload_digest is None
    assert lock.required_config_id is None


def test_config_version_lock_accepts_optional_required_digest_and_config_id():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    config_id = expected_config_id(payload_json=payload_json)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest=digest,
        required_config_id=config_id,
    )

    assert lock.required_payload_digest == digest
    assert lock.required_config_id == config_id


@pytest.mark.parametrize(
    "bad_digest",
    [
        "",
        " ",
        "abc",
        "0" * 63,
        "0" * 65,
        "g" * 64,
        "A" * 64,
    ],
)
def test_config_version_lock_rejects_malformed_required_payload_digest(bad_digest):
    with pytest.raises(ValueError, match="required_payload_digest"):
        ConfigVersionLock(
            config_kind="structure_rules",
            schema_version="1.0.0",
            config_version="2.1.0",
            required_payload_digest=bad_digest,
        )


@pytest.mark.parametrize(
    "bad_config_id",
    [
        "",
        " ",
        "abc",
        "deterministic_config",
        "deterministic_config_",
        "deterministic_config_" + "0" * 31,
        "deterministic_config_" + "0" * 33,
        "deterministic_config_" + "g" * 32,
        "other_namespace_" + "0" * 32,
        "deterministic_config_" + "A" * 32,
    ],
)
def test_config_version_lock_rejects_malformed_required_config_id(bad_config_id):
    with pytest.raises(ValueError, match="required_config_id"):
        ConfigVersionLock(
            config_kind="structure_rules",
            schema_version="1.0.0",
            config_version="2.1.0",
            required_config_id=bad_config_id,
        )


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("required_payload_digest", 123),
        ("required_config_id", 123),
    ],
)
def test_config_version_lock_rejects_non_string_optional_constraints_with_type_error(
    field_name,
    bad_value,
):
    kwargs = {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = bad_value

    with pytest.raises(TypeError, match=field_name):
        ConfigVersionLock(**kwargs)


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("config_kind", 123),
        ("schema_version", 123),
        ("config_version", 123),
    ],
)
def test_config_version_lock_rejects_non_string_required_fields_with_type_error(
    field_name,
    bad_value,
):
    kwargs = {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = bad_value

    with pytest.raises(TypeError, match=field_name):
        ConfigVersionLock(**kwargs)


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("config_kind", ""),
        ("config_kind", " "),
        ("schema_version", ""),
        ("config_version", ""),
    ],
)
def test_config_version_lock_rejects_empty_required_fields_with_value_error(
    field_name,
    bad_value,
):
    kwargs = {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = bad_value

    with pytest.raises(ValueError, match=field_name):
        ConfigVersionLock(**kwargs)


@pytest.mark.parametrize(
    "field_name,bad_version",
    [
        ("schema_version", "01.0.0"),
        ("schema_version", "1.0"),
        ("schema_version", "v1.0.0"),
        ("config_version", "01.0.0"),
        ("config_version", "1.0"),
        ("config_version", "v1.0.0"),
    ],
)
def test_config_version_lock_rejects_malformed_versions(field_name, bad_version):
    kwargs = {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
    }
    kwargs[field_name] = bad_version

    with pytest.raises(ValueError, match=field_name):
        ConfigVersionLock(**kwargs)


def test_config_version_lock_is_immutable():
    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    with pytest.raises(FrozenInstanceError):
        lock.config_version = "9.9.9"


# ---------------------------------------------------------------------------
# ConfigVersionLock satisfaction
# ---------------------------------------------------------------------------


def test_version_only_lock_is_satisfied_by_exact_matching_config():
    cfg = make_config()

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.is_satisfied_by(cfg) is True


def test_version_only_lock_rejects_config_kind_mismatch():
    payload_json = sample_payload_json()
    cfg = make_config(
        config_kind="risk_rules",
        payload_json=payload_json,
    )

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.is_satisfied_by(cfg) is False


def test_version_only_lock_rejects_schema_version_mismatch():
    payload_json = sample_payload_json()
    cfg = make_config(
        schema_version="1.1.0",
        payload_json=payload_json,
    )

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.is_satisfied_by(cfg) is False


def test_version_only_lock_rejects_config_version_mismatch():
    payload_json = sample_payload_json()
    cfg = make_config(
        config_version="2.2.0",
        payload_json=payload_json,
    )

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.is_satisfied_by(cfg) is False


def test_lock_with_required_payload_digest_requires_exact_match():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    cfg = make_config(payload_json=payload_json)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest=digest,
    )

    assert lock.is_satisfied_by(cfg) is True


def test_lock_with_required_payload_digest_rejects_mismatch():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    wrong_digest = "0" * 64
    if wrong_digest == digest:
        wrong_digest = "1" * 64

    cfg = make_config(payload_json=payload_json)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest=wrong_digest,
    )

    assert lock.is_satisfied_by(cfg) is False


def test_lock_with_required_config_id_requires_exact_match():
    payload_json = sample_payload_json()
    config_id = expected_config_id(payload_json=payload_json)
    cfg = make_config(payload_json=payload_json, config_id=config_id)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_config_id=config_id,
    )

    assert lock.is_satisfied_by(cfg) is True


def test_lock_with_required_config_id_rejects_mismatch():
    payload_json = sample_payload_json()
    config_id = expected_config_id(payload_json=payload_json)
    wrong_id = "deterministic_config_00000000000000000000000000000000"
    if wrong_id == config_id:
        wrong_id = "deterministic_config_11111111111111111111111111111111"

    cfg = make_config(payload_json=payload_json, config_id=config_id)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_config_id=wrong_id,
    )

    assert lock.is_satisfied_by(cfg) is False


def test_lock_with_digest_and_config_id_requires_both_to_match():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    config_id = expected_config_id(payload_json=payload_json)
    cfg = make_config(payload_json=payload_json, config_id=config_id)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest=digest,
        required_config_id=config_id,
    )

    assert lock.is_satisfied_by(cfg) is True


def test_lock_with_digest_and_config_id_rejects_if_either_optional_constraint_mismatches():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    config_id = expected_config_id(payload_json=payload_json)
    wrong_digest = "0" * 64
    if wrong_digest == digest:
        wrong_digest = "1" * 64

    cfg = make_config(payload_json=payload_json, config_id=config_id)

    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest=wrong_digest,
        required_config_id=config_id,
    )

    assert lock.is_satisfied_by(cfg) is False


@pytest.mark.parametrize("bad_config", [None, {}, object(), "config"])
def test_config_version_lock_is_satisfied_by_rejects_non_config_with_type_error(
    bad_config,
):
    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    with pytest.raises(TypeError, match="DeterministicConfig"):
        lock.is_satisfied_by(bad_config)


# ---------------------------------------------------------------------------
# Determinism / replayability
# ---------------------------------------------------------------------------


def test_same_config_inputs_produce_same_config_id():
    payload_json = sample_payload_json()
    cid = expected_config_id(payload_json=payload_json)

    cfg1 = make_config(payload_json=payload_json, config_id=cid)
    cfg2 = make_config(payload_json=payload_json, config_id=cid)

    assert cfg1.config_id == cfg2.config_id
    assert cfg1.payload_digest == cfg2.payload_digest
    assert cfg1 == cfg2


def test_changing_payload_changes_digest_and_config_id():
    payload_json_1 = canonical_json({"enabled": True, "threshold": 10})
    payload_json_2 = canonical_json({"enabled": True, "threshold": 11})

    digest_1 = payload_digest(payload_json_1)
    digest_2 = payload_digest(payload_json_2)

    id_1 = expected_config_id(payload_json=payload_json_1)
    id_2 = expected_config_id(payload_json=payload_json_2)

    assert digest_1 != digest_2
    assert id_1 != id_2


def test_changing_config_version_changes_config_id():
    payload_json = sample_payload_json()

    id_1 = expected_config_id(config_version="2.1.0", payload_json=payload_json)
    id_2 = expected_config_id(config_version="2.2.0", payload_json=payload_json)

    assert id_1 != id_2


def test_changing_schema_version_changes_config_id():
    payload_json = sample_payload_json()

    id_1 = expected_config_id(schema_version="1.0.0", payload_json=payload_json)
    id_2 = expected_config_id(schema_version="1.1.0", payload_json=payload_json)

    assert id_1 != id_2


def test_changing_config_kind_changes_config_id():
    payload_json = sample_payload_json()

    id_1 = expected_config_id(config_kind="structure_rules", payload_json=payload_json)
    id_2 = expected_config_id(config_kind="setup_rules", payload_json=payload_json)

    assert id_1 != id_2


# ---------------------------------------------------------------------------
# canonical_dict, aligned with existing core contract style
# ---------------------------------------------------------------------------


def test_deterministic_config_canonical_dict_returns_stable_data():
    payload_json = sample_payload_json()
    digest = payload_digest(payload_json)
    config_id = expected_config_id(payload_json=payload_json)

    cfg = make_config(
        payload_json=payload_json,
        payload_digest_value=digest,
        config_id=config_id,
    )

    assert cfg.canonical_dict() == {
        "config_id": config_id,
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
        "payload_json": payload_json,
        "payload_digest": digest,
    }


def test_config_version_lock_canonical_dict_returns_stable_data_with_constraints():
    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
        required_payload_digest="0" * 64,
        required_config_id="deterministic_config_" + "1" * 32,
    )

    assert lock.canonical_dict() == {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
        "required_payload_digest": "0" * 64,
        "required_config_id": "deterministic_config_" + "1" * 32,
    }


def test_config_version_lock_canonical_dict_includes_none_optional_constraints():
    lock = ConfigVersionLock(
        config_kind="structure_rules",
        schema_version="1.0.0",
        config_version="2.1.0",
    )

    assert lock.canonical_dict() == {
        "config_kind": "structure_rules",
        "schema_version": "1.0.0",
        "config_version": "2.1.0",
        "required_payload_digest": None,
        "required_config_id": None,
    }
