"""Optional Model Context Protocol adapter exposing version-specific read-only tools.

Requires: pip install -r requirements-mcp.txt
Run: python mcp_server.py (Streamable HTTP, typically /mcp)
For public deployment configure HTTPS and access controls before publication.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from lab import store

mcp = FastMCP(
    "Nexo Industrial | Documentación sintética", stateless_http=True, json_response=True
)


@mcp.tool()
def get_versions() -> dict:
    """Describe available corpus versions. Choose one and keep it fixed during experiments."""
    return {
        "v1": "PDF caótico: solo browsing y lectura",
        "v2": "PDF organizado: índice de área y documento identificado",
        "v3": "Markdown: búsqueda léxica por chunks y documento completo",
        "areas": store.AREAS,
        "counts": store.inventory(),
    }


@mcp.tool()
def v1_browse_folder(folder: str = "") -> dict:
    """Navigate V1 folders without semantic or global document indexes."""
    return store.browse_v1(folder)


@mcp.tool()
def v1_read_pdf(path: str) -> dict:
    """Extract one V1 PDF's text after its full path was discovered by folder browsing."""
    return store.read_v1(path)


@mcp.tool()
def v2_list_areas() -> list[str]:
    """List V2 logical areas. Follow the area index before reading PDF."""
    return store.AREAS


@mcp.tool()
def v2_list_index(area: str) -> list[dict]:
    """Read one V2 area index containing document IDs, titles and descriptions."""
    return store.v2_index(area)


@mcp.tool()
def v2_read_pdf(doc_id: str) -> dict:
    """Read one indexed V2 PDF by canonical document ID."""
    return store.read_v2(doc_id)


@mcp.tool()
def v3_search_chunks(query: str, limit: int = 5) -> list[dict]:
    """FTS5/BM25 retrieval of Markdown chunks with IDs and supporting excerpts."""
    return store.search_v3(query, limit)


@mcp.tool()
def v3_read_chunk(chunk_id: str) -> dict:
    """Read the complete supporting Markdown chunk by its source ID."""
    return store.get_chunk(chunk_id)


@mcp.tool()
def v3_read_document(doc_id: str) -> dict:
    """Read an entire V3 Markdown document with its metadata and section headings."""
    return store.read_v3(doc_id)


@mcp.tool()
def list_synthetic_examples(kind: str) -> list[dict]:
    """Get emails, tickets, or projects (kind: correos, tickets, proyectos)."""
    return store.examples(kind)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
