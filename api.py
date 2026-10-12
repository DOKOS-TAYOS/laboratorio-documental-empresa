"""Optional read-only FastAPI service for ChatGPT tools, MCP adapters, or GPT Actions.

Run separately from Streamlit: uvicorn api:app --host 0.0.0.0 --port 8000
Set LAB_API_KEY to require Authorization: Bearer <token> on /api/* endpoints.
"""

from __future__ import annotations

import os
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query

from lab import store

app = FastAPI(
    title="Nexo Industrial - Laboratorio documental",
    version="1.0.0",
    description="Corpus sintético de solo lectura. V1: exploración por carpetas; V2: índices; V3: búsqueda por chunks.",
)


def auth(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.environ.get("LAB_API_KEY", "")
    if expected and not (
        authorization
        and authorization.startswith("Bearer ")
        and secrets.compare_digest(authorization[7:], expected)
    ):
        raise HTTPException(status_code=401, detail="Se requiere token válido")


router = APIRouter(prefix="/api", dependencies=[Depends(auth)])


def reject(exc: Exception) -> None:
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, FileNotFoundError):
        raise HTTPException(status_code=404, detail="No encontrado") from exc
    raise exc


@app.get("/health", tags=["operación"])
def health() -> dict[str, str]:
    return {"status": "ok", "dataset": "sintético"}


@router.get("/catalog", tags=["general"])
def api_catalog() -> dict:
    return {
        "versions": {
            "v1": "PDFs caóticos sin índice",
            "v2": "PDFs organizados e indexados",
            "v3": "Markdown y chunks",
        },
        "areas": store.AREAS,
        "inventory": store.inventory(),
        "instructions": "Elija una versión y no mezcle resultados de otras versiones al comparar.",
    }


@router.get("/v1/browse", tags=["v1"])
def api_v1_browse(folder: str = "") -> dict:
    """List files and subfolders within a chosen folder (no global document index)."""
    try:
        return store.browse_v1(folder)
    except (ValueError, FileNotFoundError) as exc:
        reject(exc)


@router.get("/v1/read", tags=["v1"])
def api_v1_read(path: str) -> dict:
    """Extract text from one PDF after its path has been discovered by browsing."""
    try:
        return store.read_v1(path)
    except (ValueError, FileNotFoundError) as exc:
        reject(exc)


@router.get("/v2/areas", tags=["v2"])
def api_v2_areas() -> dict:
    return {"areas": store.AREAS, "index": "data/v2_indexada/INDICE_GENERAL.md"}


@router.get("/v2/index/{area}", tags=["v2"])
def api_v2_index(area: str) -> dict:
    try:
        return {"area": area, "documents": store.v2_index(area)}
    except ValueError as exc:
        reject(exc)


@router.get("/v2/document/{doc_id}", tags=["v2"])
def api_v2_doc(doc_id: str) -> dict:
    try:
        return store.read_v2(doc_id)
    except (ValueError, FileNotFoundError) as exc:
        reject(exc)


@router.get("/v3/search", tags=["v3"])
def api_v3_search(
    query: str = Query(min_length=2, max_length=300),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict:
    return {"query": query, "results": store.search_v3(query, limit)}


@router.get("/v3/chunk/{chunk_id}", tags=["v3"])
def api_v3_chunk(chunk_id: str) -> dict:
    try:
        return store.get_chunk(chunk_id)
    except FileNotFoundError as exc:
        reject(exc)


@router.get("/v3/document/{doc_id}", tags=["v3"])
def api_v3_doc(doc_id: str) -> dict:
    try:
        return store.read_v3(doc_id)
    except FileNotFoundError as exc:
        reject(exc)


@router.get("/examples/{kind}", tags=["ejemplos"])
def api_examples(kind: str) -> dict:
    try:
        return {"kind": kind, "records": store.examples(kind)}
    except ValueError as exc:
        reject(exc)


app.include_router(router)
