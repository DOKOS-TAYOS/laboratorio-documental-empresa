"""Corpus parity and adapter regression checks."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api import app
from lab import store


@pytest.fixture(autouse=True)
def public_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LAB_API_KEY", raising=False)


def test_inventory_and_three_versions() -> None:
    inv = store.inventory()
    assert inv["documentos_canonicos"] == 100
    assert inv["pdf_v1"] == 108
    assert inv["pdf_v2"] == 100
    assert inv["markdown_v3"] == 100
    assert inv["chunks_v3"] == 300
    assert len(store.catalog()) == 100
    assert len(set(x["id"] for x in store.catalog())) == 100
    assert all(len(store.v2_index(area)) == 10 for area in store.AREAS)
    assert len(store.chunks()) == 300


def test_pdf_content_parity() -> None:
    """PDF bytes are bitwise identical between V1 and V2 for each canonical doc."""
    for d in store.catalog():
        v1 = store.safe_path(store.VERSION_DIRS["v1"], d["v1_path"])
        v2 = store.safe_path(store.VERSION_DIRS["v2"], d["v2_path"])
        assert v1.read_bytes() == v2.read_bytes()
        assert store.safe_path(store.VERSION_DIRS["v3"], d["v3_path"]).is_file()


def test_full_document_text() -> None:
    assert "Restauración de copias de seguridad" in store.read_v2("PROC-035")["text"]
    md = store.read_v3("PROC-035")["markdown"]
    assert "Restauración de copias de seguridad" in md
    assert "Gestión de excepciones" in md


def test_v3_retrieval() -> None:
    results = store.search_v3("restauración de copias de seguridad")
    assert results and any(r["document_id"] == "PROC-035" for r in results)
    assert results[0]["chunk_id"] in store.chunks()
    assert store.search_v3("") == []


def test_path_traversal_rejected() -> None:
    for path in ("../../api.py", "/etc/passwd", "\\..\\..\\etc\\passwd"):
        with pytest.raises(ValueError):
            store.safe_path(store.VERSION_DIRS["v1"], path)


def test_api_read_only_and_versions() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    spec = client.get("/openapi.json").json()
    assert "/api/v3/search" in spec["paths"]
    assert all(
        set(path_spec).issubset({"get", "parameters"})
        for path_spec in spec["paths"].values()
    )
    assert client.get("/api/v1/browse").status_code == 200
    assert (
        client.get("/api/v1/read", params={"path": "../../api.py"}).status_code == 400
    )
    assert len(client.get("/api/v2/index/informatica").json()["documents"]) == 10
    assert client.get("/api/v2/document/PROC-035").status_code == 200
    assert client.get("/api/v3/search", params={"query": "copias de seguridad"}).json()[
        "results"
    ]
    assert len(client.get("/api/examples/tickets").json()["records"]) == 25


def test_bearer_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAB_API_KEY", "test-only")
    client = TestClient(app)
    assert client.get("/api/catalog").status_code == 401
    assert (
        client.get(
            "/api/catalog", headers={"Authorization": "Bearer test-only"}
        ).status_code
        == 200
    )
    assert client.get("/health").status_code == 200
