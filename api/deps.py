"""FastAPI dependency providers."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from smart_money.application.dashboard_macro_read_index import DashboardMacroReadIndex


def get_macro_read_index(request: Request) -> DashboardMacroReadIndex:
    index = getattr(request.app.state, "macro_read_index", None)
    if not isinstance(index, DashboardMacroReadIndex):
        raise RuntimeError("dashboard macro read index is not initialized")
    return index


MacroReadIndexDep = Annotated[DashboardMacroReadIndex, Depends(get_macro_read_index)]
