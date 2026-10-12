#!/bin/sh
# Run from the repository root, including inside python:3.12-slim.
set -eu

export PYTHONDONTWRITEBYTECODE=1
python -m venv /tmp/.venv
. /tmp/.venv/bin/activate

# First check the web with only the dependencies installed by Community Cloud.
python -m pip install --disable-pip-version-check -q -r requirements.txt
python -m pip check
python - <<'PY'
from streamlit.testing.v1 import AppTest

app = AppTest.from_file('streamlit_app.py', default_timeout=15).run()
assert not app.exception
assert app.main.title[0].value == 'Laboratorio documental empresarial'
print('Streamlit starts with only the Cloud dependencies.')
PY

python -m pip install --disable-pip-version-check -q -r requirements-dev.txt
python -m pip check
python -m ruff check . --no-cache
python -m ruff format . --check --no-cache
python -m pytest -q -p no:cacheprovider
