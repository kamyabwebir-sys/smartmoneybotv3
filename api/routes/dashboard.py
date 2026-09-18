"""Dashboard read endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..deps import MacroReadIndexDep

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=None)
def list_dashboard(
    index: MacroReadIndexDep,
    query: str = Query(""),
    subject_kind: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    page = index.page(query=query, subject_kind=subject_kind, status=status, offset=offset, limit=limit)
    return page.canonical_dict()


@router.get("/{subject_id}", response_model=None)
def get_subject_detail(
    subject_id: str,
    index: MacroReadIndexDep,
    subject_kind: str | None = Query(None),
):
    try:
        detail = index.detail_for_subject(subject_id, subject_kind=subject_kind)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"subject not found: {subject_id}"
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail=f"ambiguous or invalid subject_id: {subject_id}"
        ) from exc

    return {
        "model_id": detail.response.model_id,
        "report_id": detail.response.report_id,
        "explanation_id": detail.response.explanation_id,
        "subject_id": detail.response.subject_id,
        "markdown": detail.response.markdown,
        "snapshot_content_hash": detail.response.snapshot_content_hash,
        "schema_version": detail.response.schema_version,
    }
