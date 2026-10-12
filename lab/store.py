"""Read-only storage and retrieval for three documentary representations."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

from pypdf import PdfReader

DATA = Path(__file__).resolve().parents[1] / "data"
VERSION_DIRS = {
    "v1": DATA / "v1_caotica",
    "v2": DATA / "v2_indexada",
    "v3": DATA / "v3_markdown",
}
AREAS = [
    "operaciones",
    "calidad",
    "mantenimiento",
    "informatica",
    "seguridad",
    "logistica",
    "compras",
    "personas",
    "proyectos",
    "produccion",
]


@lru_cache(maxsize=1)
def catalog() -> list[dict[str, Any]]:
    return json.loads(
        (DATA / "internal" / "correspondencias.json").read_text(encoding="utf-8")
    )


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a relative corpus path without directory traversal or symlinks."""
    relative = relative.replace("\\", "/")
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("Ruta no permitida")
    final = (root / p).resolve()
    if not final.is_relative_to(root.resolve()):
        raise ValueError("Ruta no permitida")
    return final


def browse_v1(folder: str = "") -> dict[str, Any]:
    root = VERSION_DIRS["v1"]
    path = safe_path(root, folder)
    if not path.is_dir():
        raise FileNotFoundError(folder)
    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    return {
        "folder": folder,
        "folders": [p.relative_to(root).as_posix() for p in entries if p.is_dir()],
        "files": [
            p.relative_to(root).as_posix()
            for p in entries
            if p.is_file() and p.suffix.lower() == ".pdf"
        ],
    }


def pdf_text(path: Path) -> str:
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise FileNotFoundError(str(path))
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def read_v1(path: str) -> dict[str, str]:
    resolved = safe_path(VERSION_DIRS["v1"], path)
    return {"path": path, "text": pdf_text(resolved)}


def v2_index(area: str) -> list[dict[str, str]]:
    if area not in AREAS:
        raise ValueError("Área no válida")
    with (VERSION_DIRS["v2"] / area / "indice.csv").open(
        encoding="utf-8", newline=""
    ) as fh:
        return list(csv.DictReader(fh))


def get_document(doc_id: str) -> dict[str, Any]:
    try:
        return next(d for d in catalog() if d["id"] == doc_id)
    except StopIteration as exc:
        raise FileNotFoundError(doc_id) from exc


def read_v2(doc_id: str) -> dict[str, str]:
    d = get_document(doc_id)
    return {
        "id": d["id"],
        "title": d["title"],
        "area": d["area"],
        "version": d["version"],
        "path": d["v2_path"],
        "text": pdf_text(safe_path(VERSION_DIRS["v2"], d["v2_path"])),
    }


def read_v3(doc_id: str) -> dict[str, str]:
    d = get_document(doc_id)
    return {
        "id": d["id"],
        "title": d["title"],
        "area": d["area"],
        "path": d["v3_path"],
        "markdown": safe_path(VERSION_DIRS["v3"], d["v3_path"]).read_text(
            encoding="utf-8"
        ),
    }


@lru_cache(maxsize=1)
def chunks() -> dict[str, dict[str, Any]]:
    return {
        c["chunk_id"]: c
        for c in json.loads(
            (VERSION_DIRS["v3"] / "chunks.json").read_text(encoding="utf-8")
        )
    }


def search_v3(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Lexical retrieval with BM25, not an embedding or semantic search service."""
    tokens = re.findall(r"\w+", query.lower(), flags=re.UNICODE)[:12]
    if not tokens or not 1 <= limit <= 10:
        return []
    match = " OR ".join('"' + t.replace('"', "") + '"' for t in tokens)
    database = (VERSION_DIRS["v3"] / "search.sqlite").resolve().as_uri()
    con = sqlite3.connect(f"{database}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT chunk_id, document_id, area, title, bm25(chunks) AS score "
            "FROM chunks WHERE chunks MATCH ? ORDER BY score ASC LIMIT ?",
            (match, limit),
        ).fetchall()
    finally:
        con.close()
    return [
        dict(
            chunk_id=c,
            document_id=d,
            area=area,
            title=title,
            score=round(score, 5),
            headings=chunks()[c]["headings"],
            excerpt=chunks()[c]["text"][:2200],
        )
        for c, d, area, title, score in rows
    ]


def get_chunk(chunk_id: str) -> dict[str, Any]:
    if chunk_id not in chunks():
        raise FileNotFoundError(chunk_id)
    return chunks()[chunk_id]


def examples(kind: str) -> list[dict[str, Any]]:
    if kind not in ("correos", "tickets", "proyectos"):
        raise ValueError("Tipo no válido")
    return json.loads((DATA / f"{kind}.json").read_text(encoding="utf-8"))


def inventory() -> dict[str, int]:
    return json.loads((DATA / "inventario.json").read_text(encoding="utf-8"))
