"""Build isolated documentary snapshots for use as chat file attachments."""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from .store import DATA, VERSION_DIRS

_SHARED = ("correos.json", "tickets.json", "proyectos.json")

PUBLIC_RELEASE_URL = (
    "https://github.com/DOKOS-TAYOS/laboratorio-documental-datos"
    "/releases/download/v1.0.0"
)


def public_bundle_url(version: str) -> str:
    """Return the direct URL of the published, versioned corpus snapshot."""
    if version not in VERSION_DIRS:
        raise ValueError("Versión no válida")
    return f"{PUBLIC_RELEASE_URL}/laboratorio_{version}_chatgpt.zip"


def export_zip(version: str) -> bytes:
    """Return a ZIP containing only the requested version and shared examples.

    Excludes internal answer keys, other version indexes, and application source.
    """
    if version not in VERSION_DIRS:
        raise ValueError("Versión no válida")

    root = VERSION_DIRS[version]
    target = BytesIO()
    with ZipFile(
        target, mode="w", compression=ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(DATA).as_posix())
        for name in _SHARED:
            archive.write(DATA / name, arcname=name)
    return target.getvalue()
