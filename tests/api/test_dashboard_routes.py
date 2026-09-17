"""Integration tests for dashboard API endpoints.

Uses FakeMacroReadIndex injected via dependency_overrides so no real
infrastructure (DB, provider) is required.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from smart_money.application.dashboard_macro_read_endpoint import DashboardMacroReadResponse
from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
    DashboardMacroReadPage,
)
from api.main import create_app
from api.deps import get_macro_read_index


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_HASH_A = "a" * 64  # valid 64-char lowercase hex
_HASH_B = "b" * 64
_HASH_C = "c" * 64




def _contract_markdown_base(  # B3-SIG
    subject_id=None,
    subject_kind=None,
    status_marker=None,
    *,
    metric='cpi',
    status='confirmed',
    observed_at='2026-01-01T00:00:00+00:00',
    value='1.0',
    unit='percent',
    observation_count=1,
    conflicted_count=0,
    unknown_count=0,
) -> str:
    if subject_id is not None:
        metric = subject_id
    if status_marker is not None:
        status = status_marker
    _ = subject_kind  # markdown contract has no subject-kind line (prefixes=[])
    """Canonical dashboard markdown generated from the domain parser contract."""
    lines: list[str] = ["# \u062f\u0627\u0634\u0628\u0648\u0631\u062f", ""]
    lines.append("")
    lines.append("| شاخص | وضعیت | زمان مشاهده | مقدار | واحد |")
    lines.append("| --- | --- | --- | --- | --- |")
    cells = [f'{metric}', f'{status}', f'{observed_at}', f'{value}', f'{unit}']
    lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"| تعداد مشاهده\u200cها | {observation_count} |")
    lines.append(f"| تعداد موارد متناقض | {conflicted_count} |")
    lines.append(f"| تعداد موارد نامشخص | {unknown_count} |")
    lines.append("")
    return "\n".join(lines)

def _resp(
    subject_id: str,
    model_id: str = "model-x",
    subject_kind: str = "equity",
    status_marker: str = "active",
    idx: int = 1,
) -> DashboardMacroReadResponse:
    """Build a minimal valid DashboardMacroReadResponse."""
    hash_char = hex(idx % 16)[-1]
    return DashboardMacroReadResponse(
        model_id=model_id,
        report_id=f"report-{idx:04d}",
        explanation_id=f"expl-{idx:04d}",
        subject_id=subject_id,
        markdown=_contract_markdown(subject_id, subject_kind, status_marker),
        snapshot_content_hash=hash_char * 64,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def sample_responses() -> list[DashboardMacroReadResponse]:
    return [
        _resp("AAPL",  model_id="model-alpha", subject_kind="equity",   status_marker="active",   idx=1),
        _resp("TSLA",  model_id="model-alpha", subject_kind="equity",   status_marker="inactive", idx=2),
        _resp("BTC",   model_id="model-beta",  subject_kind="crypto",   status_marker="active",   idx=3),
        _resp("ETH",   model_id="model-beta",  subject_kind="crypto",   status_marker="active",   idx=4),
        _resp("GOLD",  model_id="model-gamma", subject_kind="commodity", status_marker="pending", idx=5),
    ]


@pytest.fixture()
def fake_index(sample_responses: list[DashboardMacroReadResponse]) -> DashboardMacroReadIndex:
    return DashboardMacroReadIndex.from_responses(sample_responses)


@pytest.fixture()
def client(fake_index: DashboardMacroReadIndex) -> TestClient:
    """TestClient with the real index injected — no lifespan, no DB."""
    app = create_app(lifespan_enabled=False)
    app.dependency_overrides[get_macro_read_index] = lambda: fake_index
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# GET /dashboard/ — listing & pagination
# ─────────────────────────────────────────────────────────────────────────────

class TestListEndpoint:
    def test_returns_200(self, client: TestClient) -> None:
        r = client.get("/dashboard/")
        assert r.status_code == 200

    def test_default_returns_all_items(
        self, client: TestClient, sample_responses: list[DashboardMacroReadResponse]
    ) -> None:
        r = client.get("/dashboard/")
        body = r.json()
        assert body["total_count"] == len(sample_responses)
        assert len(body["items"]) == len(sample_responses)

    def test_schema_keys_present(self, client: TestClient) -> None:
        r = client.get("/dashboard/")
        body = r.json()
        for key in ("items", "total_count", "offset", "limit", "query"):
            assert key in body, f"Missing key: {key}"

    def test_item_schema_keys(self, client: TestClient) -> None:
        r = client.get("/dashboard/")
        item = r.json()["items"][0]
        expected = {
            "model_id", "report_id", "explanation_id",
            "subject_id", "markdown", "snapshot_content_hash", "schema_version",
        }
        assert expected.issubset(item.keys())

    def test_snapshot_content_hash_is_64_hex(self, client: TestClient) -> None:
        r = client.get("/dashboard/")
        for item in r.json()["items"]:
            h = item["snapshot_content_hash"]
            assert len(h) == 64, f"Hash length {len(h)} for {item['subject_id']}"
            assert all(c in "0123456789abcdef" for c in h), f"Non-hex char in hash: {h!r}"

    def test_pagination_limit(self, client: TestClient) -> None:
        r = client.get("/dashboard/?limit=2&offset=0")
        body = r.json()
        assert len(body["items"]) == 2
        assert body["total_count"] == 5
        assert body["limit"] == 2
        assert body["offset"] == 0

    def test_pagination_offset(self, client: TestClient) -> None:
        r_full = client.get("/dashboard/?limit=50")
        all_ids = [i["subject_id"] for i in r_full.json()["items"]]

        r_paged = client.get("/dashboard/?limit=2&offset=2")
        paged_ids = [i["subject_id"] for i in r_paged.json()["items"]]
        assert paged_ids == all_ids[2:4]

    def test_pagination_beyond_end_returns_empty(self, client: TestClient) -> None:
        r = client.get("/dashboard/?limit=10&offset=100")
        body = r.json()
        assert body["items"] == []
        assert body["total_count"] == 5

    def test_query_filter_casefold(self, client: TestClient) -> None:
        """Filter is casefold on subject_id/model_id."""
        r = client.get("/dashboard/?query=aapl")
        body = r.json()
        assert body["total_count"] == 1
        assert body["items"][0]["subject_id"] == "AAPL"

    def test_query_filter_no_match(self, client: TestClient) -> None:
        r = client.get("/dashboard/?query=ZZZNOTEXIST")
        body = r.json()
        assert body["total_count"] == 0
        assert body["items"] == []

    def test_query_filter_partial_match(self, client: TestClient) -> None:
        """model-alpha covers AAPL and TSLA."""
        r = client.get("/dashboard/?query=model-alpha")
        body = r.json()
        assert body["total_count"] == 2
        subject_ids = {i["subject_id"] for i in body["items"]}
        assert subject_ids == {"AAPL", "TSLA"}

    def test_empty_query_returns_all(self, client: TestClient) -> None:
        r = client.get("/dashboard/?query=")
        assert r.json()["total_count"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# GET /dashboard/{subject_id} — detail
# ─────────────────────────────────────────────────────────────────────────────

class TestDetailEndpoint:
    def test_returns_200_for_existing(self, client: TestClient) -> None:
        r = client.get("/dashboard/AAPL")
        assert r.status_code == 200

    def test_returns_404_for_missing(self, client: TestClient) -> None:
        r = client.get("/dashboard/NONEXISTENT_TICKER")
        assert r.status_code == 404

    def test_404_body_contains_detail(self, client: TestClient) -> None:
        r = client.get("/dashboard/NONEXISTENT_TICKER")
        body = r.json()
        assert "detail" in body

    def test_detail_schema_complete(self, client: TestClient) -> None:
        r = client.get("/dashboard/AAPL")
        body = r.json()
        for key in (
            "model_id", "report_id", "explanation_id",
            "subject_id", "markdown", "snapshot_content_hash", "schema_version",
        ):
            assert key in body, f"Missing key: {key}"

    def test_detail_subject_id_matches(self, client: TestClient) -> None:
        for sid in ("AAPL", "TSLA", "BTC", "ETH", "GOLD"):
            r = client.get(f"/dashboard/{sid}")
            assert r.status_code == 200
            assert r.json()["subject_id"] == sid

    def test_detail_snapshot_hash_is_64_hex(self, client: TestClient) -> None:
        r = client.get("/dashboard/BTC")
        h = r.json()["snapshot_content_hash"]
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_detail_schema_version_correct(self, client: TestClient) -> None:
        r = client.get("/dashboard/ETH")
        assert r.json()["schema_version"] == "dashboard_macro_read_response.v1"

    def test_detail_model_id_matches_fixture(
        self, client: TestClient, sample_responses: list[DashboardMacroReadResponse]
    ) -> None:
        expected = {rsp.subject_id: rsp.model_id for rsp in sample_responses}
        for sid, mid in expected.items():
            r = client.get(f"/dashboard/{sid}")
            assert r.json()["model_id"] == mid


# ─────────────────────────────────────────────────────────────────────────────
# Consistency: list ↔ detail
# ─────────────────────────────────────────────────────────────────────────────

class TestListDetailConsistency:
    def test_list_ids_match_detail_responses(self, client: TestClient) -> None:
        """Every subject_id from the list must resolve in the detail endpoint."""
        list_body = client.get("/dashboard/").json()
        for item in list_body["items"]:
            sid = item["subject_id"]
            r = client.get(f"/dashboard/{sid}")
            assert r.status_code == 200, f"Detail 404 for subject_id={sid!r}"

    def test_list_item_equals_detail_item(self, client: TestClient) -> None:
        """Field values in the list must match the detail endpoint for same subject."""
        list_body = client.get("/dashboard/").json()
        for list_item in list_body["items"]:
            sid = list_item["subject_id"]
            detail = client.get(f"/dashboard/{sid}").json()
            for key in (
                "model_id", "report_id", "explanation_id",
                "snapshot_content_hash", "schema_version",
            ):
                assert list_item[key] == detail[key], (
                    f"Mismatch on {key!r} for subject_id={sid!r}: "
                    f"list={list_item[key]!r}  detail={detail[key]!r}"
                )

    def test_total_count_stable_across_requests(self, client: TestClient) -> None:
        """Index is immutable (frozen dataclass): two identical requests return same count."""
        r1 = client.get("/dashboard/").json()["total_count"]
        r2 = client.get("/dashboard/").json()["total_count"]
        assert r1 == r2

# === B4: contract markdown header injection (idempotent wrapper) ===
_CONTRACT_PREFIX_KIND = "- نوع موضوع: "
_CONTRACT_PREFIX_METRIC = "- شاخص: "
_CONTRACT_PREFIX_STATUS = "- وضعیت: "
_CONTRACT_PREFIXES = (
    _CONTRACT_PREFIX_KIND,
    _CONTRACT_PREFIX_METRIC,
    _CONTRACT_PREFIX_STATUS,
)


def _contract_markdown(
    subject_kind: str = "macro",
    metric: str = "macro-subject",
    status: str = "ok",
    *,
    markdown: str | None = None,
) -> str:
    """Deterministic markdown that always declares subject kind / metric / status."""
    base = _contract_markdown_base() if markdown is None else markdown
    kept = [
        line
        for line in base.splitlines()
        if not line.lstrip().startswith(_CONTRACT_PREFIXES)
    ]
    headers = [
        f"{_CONTRACT_PREFIX_KIND}`{subject_kind}`",
        f"{_CONTRACT_PREFIX_METRIC}`{metric}`",
        f"{_CONTRACT_PREFIX_STATUS}`{status}`",
    ]
    at = 1 if kept and kept[0].lstrip().startswith("#") else 0
    return "\n".join(kept[:at] + headers + kept[at:]).rstrip("\n") + "\n"
