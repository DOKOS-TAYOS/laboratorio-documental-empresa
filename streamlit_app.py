"""Small human browser for the same synthetic datasets queried by the API."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab import store
from lab.exports import export_zip, public_bundle_url

st.set_page_config(
    page_title="Nexo Industrial | Laboratorio de documentación", layout="wide"
)
st.sidebar.title("Nexo Industrial")
st.sidebar.caption("Empresa y contenidos completamente ficticios")
version = st.sidebar.radio(
    "Versión documental",
    ["V1 · Caótica", "V2 · Indexada", "V3 · Markdown + chunks"],
    index=0,
)
mode = version[:2].lower()


@st.cache_data(show_spinner=False, max_entries=3)
def bundle_for_version(selected: str) -> bytes:
    return export_zip(selected)


def home() -> None:
    st.title("Laboratorio documental empresarial")
    st.markdown(
        "Explore el mismo conocimiento en tres estructuras diferentes. Los documentos, los correos, las incidencias y los proyectos son **sintéticos**."
    )
    inv = store.inventory()
    a, b, c, d = st.columns(4)
    a.metric("Procedimientos canónicos", inv["documentos_canonicos"])
    b.metric("Correos", inv["correos"])
    c.metric("Tickets", inv["tickets"])
    d.metric("Proyectos", inv["proyectos"])
    st.subheader("Experimento de recuperación")
    st.write(
        "Objetivo: localizar quién aprueba una excepción, qué pasos debe seguir el equipo y qué registro debe conservarse."
    )
    st.info(
        "En V1 se navega por carpetas; en V2 se consultan índices; en V3 se recuperan fragmentos. No se debe utilizar conocimiento de otra versión durante la comparación."
    )
    st.markdown(
        "**Ejercicio común:** Identifique el procedimiento relativo a la restauración de copias de seguridad y cite el rol responsable y el proceso de cierre."
    )


def examples_page(kind: str, label: str) -> None:
    st.title(label)
    records = store.examples(kind)
    st.caption(f"{len(records)} ejemplos empresariales generados artificialmente.")
    labels = [r["id"] + " · " + (r.get("asunto") or r.get("nombre")) for r in records]
    choice = st.selectbox(
        "Seleccionar registro", range(len(records)), format_func=lambda i: labels[i]
    )
    item = records[choice]
    st.json(item, expanded=True)
    if kind == "correos":
        st.subheader(item["asunto"])
        st.write(item["cuerpo"])
    st.caption(
        "Los identificadores PROC vinculan estos ejemplos con los procedimientos documentales."
    )


def emails() -> None:
    examples_page("correos", "Ejemplos de correos")


def tickets() -> None:
    examples_page("tickets", "Incidencias y tickets")


def projects() -> None:
    examples_page("proyectos", "Seguimiento de proyectos")


def docs_page() -> None:
    st.title("Biblioteca de documentación")
    st.caption(f"Vista seleccionada: {version}.")
    filename = f"laboratorio_{mode}_chatgpt.zip"
    st.download_button(
        "Descargar esta biblioteca completa (ZIP)",
        data=bundle_for_version(mode),
        file_name=filename,
        mime="application/zip",
        help="Descarga solo la versión seleccionada y los ejemplos compartidos. No incluye respuestas de evaluación.",
    )
    st.caption(
        "Para trabajar con ChatGPT, adjunte este ZIP desde Biblioteca en una conversación. Cada versión debe analizarse por separado."
    )
    direct_url = public_bundle_url(mode)
    st.link_button("Descarga directa desde GitHub (ZIP)", direct_url)
    with st.expander("Enlace para un asistente o una descarga automática"):
        st.write(
            "Este enlace descarga una copia fija de la biblioteca sin abrir Streamlit "
            "ni iniciar sesión en GitHub. Puede copiarlo y dárselo a un asistente "
            "que tenga herramientas para descargar y abrir archivos. "
            "Si el asistente no puede descargarlo, adjunte el ZIP a la conversación."
        )
        st.code(direct_url, language=None)
        st.caption("Edición publicada: v1.0.0. No incluye respuestas de evaluación.")
        st.caption("Cada ZIP incluye también 20 correos, 25 tickets y 10 proyectos.")
    if mode == "v1":
        st.warning(
            "No hay índice, buscador de contenido ni metadatos de clasificación. Hay carpetas ambiguas y copias obsoletas."
        )
        path = st.session_state.get("v1_folder", "")
        try:
            entries = store.browse_v1(path)
        except (ValueError, FileNotFoundError):
            path = ""
            st.session_state["v1_folder"] = ""
            entries = store.browse_v1("")
        st.code("/" + path)
        if path and st.button("Subir una carpeta"):
            st.session_state["v1_folder"] = (
                Path(path).parent.as_posix() if str(Path(path).parent) != "." else ""
            )
            st.rerun()
        if entries["folders"]:
            st.markdown("**Subcarpetas**")
            for folder in entries["folders"]:
                name = Path(folder).name
                if st.button(
                    "Carpeta: " + name, key="folder_" + folder, width="stretch"
                ):
                    st.session_state["v1_folder"] = folder
                    st.rerun()
        if entries["files"]:
            selected = st.selectbox(
                "Archivos PDF", entries["files"], format_func=lambda f: Path(f).name
            )
            docpath = store.safe_path(store.VERSION_DIRS["v1"], selected)
            st.download_button(
                "Abrir / descargar PDF",
                data=docpath.read_bytes(),
                file_name=docpath.name,
                mime="application/pdf",
            )
            with st.expander("Extraer texto del PDF para lectura", expanded=False):
                st.text(store.pdf_text(docpath))
        if not entries["files"] and not entries["folders"]:
            st.info("Esta carpeta está vacía.")
    elif mode == "v2":
        st.success(
            "Índice general, 10 índices por área y 100 PDFs referenciados por identificador."
        )
        area = st.selectbox("Área empresarial", store.AREAS)
        rows = store.v2_index(area)
        st.dataframe(
            [{k: r[k] for k in ("id", "title", "summary", "related")} for r in rows],
            hide_index=True,
            width="stretch",
        )
        docid = st.selectbox(
            "Abrir procedimiento",
            [r["id"] for r in rows],
            format_func=lambda s: next(r["title"] for r in rows if r["id"] == s),
        )
        doc = store.read_v2(docid)
        st.subheader(doc["id"] + " · " + doc["title"])
        st.text(doc["text"])
        path = store.safe_path(store.VERSION_DIRS["v2"], doc["path"])
        st.download_button(
            "Descargar PDF",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/pdf",
        )
    else:
        st.success(
            "100 Markdown, metadatos de origen, 300 chunks y búsqueda FTS5/BM25."
        )
        query = st.text_input(
            "Buscar en los fragmentos", value="restauración copias de seguridad"
        )
        results = store.search_v3(query, limit=8) if len(query.strip()) >= 2 else []
        for result in results:
            with st.expander(
                f"{result['document_id']} · {result['title']} · {result['chunk_id']}"
            ):
                st.caption(" / ".join(result["headings"]))
                st.markdown(result["excerpt"])
        st.divider()
        area = st.selectbox("O explorar por índice", store.AREAS)
        docid = st.selectbox(
            "Documento Markdown", [r["id"] for r in store.v2_index(area)]
        )
        doc = store.read_v3(docid)
        st.markdown(doc["markdown"])
        st.download_button(
            "Descargar Markdown",
            data=doc["markdown"],
            file_name=docid + ".md",
            mime="text/markdown",
        )


def comparison() -> None:
    st.title("Comparación de las tres versiones")
    st.table(
        [
            {
                "Versión": "V1",
                "Formato": "PDF",
                "Organización": "Carpetas erráticas",
                "Acceso IA": "Explorar carpetas y extraer PDF",
                "Búsqueda": "No disponible",
            },
            {
                "Versión": "V2",
                "Formato": "PDF",
                "Organización": "Índices de área + CSV",
                "Acceso IA": "Índice y documento por ID",
                "Búsqueda": "Por metadatos/indexación",
            },
            {
                "Versión": "V3",
                "Formato": "Markdown",
                "Organización": "Metadatos + chunks",
                "Acceso IA": "Búsqueda BM25 y documentos",
                "Búsqueda": "Texto completo",
            },
        ]
    )
    st.subheader("Preguntas de evaluación")
    st.markdown(
        "1. ¿Quién aprueba excepciones en la restauración de copias de seguridad?\n"
        "2. ¿Qué evidencia requiere el cierre de una avería urgente?\n"
        "3. ¿Cómo se vincula una incidencia de calidad con un procedimiento?"
    )
    st.caption(
        "Para comparar tiempos, trazas y aciertos debe utilizarse el mismo cuestionario en las tres versiones y no mezclar herramientas."
    )


def main() -> None:
    page = st.navigation(
        [
            st.Page(home, title="Inicio", icon=":material/home:"),
            st.Page(docs_page, title="Documentación", icon=":material/folder_open:"),
            st.Page(emails, title="Correos", icon=":material/mail:"),
            st.Page(tickets, title="Tickets", icon=":material/assignment:"),
            st.Page(projects, title="Proyectos", icon=":material/calendar_month:"),
            st.Page(comparison, title="Comparación", icon=":material/compare_arrows:"),
        ]
    )
    page.run()


if __name__ == "__main__":
    main()
