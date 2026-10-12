"""Exercise the actual web pages without starting a separate web server."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def page_app(function_name: str) -> AppTest:
    # run_path gives every rerun fresh page globals and the real sidebar widgets.
    source = (
        "import runpy\n"
        f"namespace = runpy.run_path({str(APP)!r})\n"
        f"namespace[{function_name!r}]()\n"
    )
    return AppTest.from_string(source, default_timeout=15)


def test_entrypoint() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert app.main.title[0].value == "Laboratorio documental empresarial"


@pytest.mark.parametrize(
    "page", ["home", "emails", "tickets", "projects", "comparison"]
)
def test_pages(page: str) -> None:
    app = page_app(page).run()
    assert not app.exception
    assert len(app.main.title) == 1


@pytest.mark.parametrize(
    "version", ["V1 · Caótica", "V2 · Indexada", "V3 · Markdown + chunks"]
)
def test_documentation_versions(version: str) -> None:
    app = page_app("docs_page").run()
    app.sidebar.radio[0].set_value(version).run()
    assert not app.exception
    assert app.main.title[0].value == "Biblioteca de documentación"
    assert len(app.get("download_button")) >= 1
    assert app.code[0].value.endswith(f"laboratorio_{version[:2].lower()}_chatgpt.zip")
    if version.startswith("V1"):
        app.button[0].click().run()
        assert not app.exception
        assert app.code[-1].value.startswith("/") and app.code[-1].value != "/"
    elif version.startswith("V2"):
        assert len(app.dataframe[0].value) == 10
        app.selectbox[0].set_value("informatica").run()
        assert not app.exception
    else:
        assert any(item.label.startswith("PROC-") for item in app.expander)
        app.text_input[0].set_value("zzzzsinresultadoszzzz").run()
        assert not app.exception
        assert not any(item.label.startswith("PROC-") for item in app.expander)
