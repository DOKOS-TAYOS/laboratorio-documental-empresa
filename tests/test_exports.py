"""Verify ChatGPT library ZIPs are clean and independently useful."""

from __future__ import annotations

import json
from io import BytesIO
from zipfile import ZipFile

import pytest

from lab.exports import export_zip


@pytest.mark.parametrize(
    "version,root,pdfs",
    [
        ("v1", "v1_caotica/", 108),
        ("v2", "v2_indexada/", 100),
        ("v3", "v3_markdown/", 0),
    ],
)
def test_export_version_isolated(version: str, root: str, pdfs: int) -> None:
    with ZipFile(BytesIO(export_zip(version))) as archive:
        paths = archive.namelist()
        assert archive.testzip() is None
        for name, count in (
            ("correos.json", 20),
            ("tickets.json", 25),
            ("proyectos.json", 10),
        ):
            assert len(json.loads(archive.read(name))) == count
        assert sum(path.endswith(".pdf") for path in paths) == pdfs
        assert all(
            path.startswith(root)
            or path in ("correos.json", "tickets.json", "proyectos.json")
            for path in paths
        )
        assert all(
            path not in ("correspondencias.json", "evaluacion.json", "inventario.json")
            for path in paths
        )
        assert all("/internal/" not in path for path in paths)
        if version == "v1":
            assert not any("indice" in path.lower() for path in paths)
        if version == "v2":
            assert root + "INDICE_GENERAL.md" in paths
        if version == "v3":
            assert root + "chunks.json" in paths
            assert root + "search.sqlite" in paths
            assert sum(path.endswith(".md") for path in paths) == 111


def test_invalid_version_rejected() -> None:
    with pytest.raises(ValueError):
        export_zip("../internal")
