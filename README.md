# Laboratorio de documentación empresarial para humanos e IA

**Nexo Industrial** es una empresa totalmente ficticia. Este repositorio presenta tres
representaciones de un corpus idéntico de **100 procedimientos**. Su propósito es comparar
cómo personas y asistentes con herramientas encuentran información empresarial bajo
condiciones de organización documental diferentes.

## Contenido

| Vista | Datos | Cómo se accede | Limitaciones intencionadas |
|---|---|---|---|
| V1: caótica | 100 PDFs canónicos + 8 copias obsoletas | Exploración por carpetas y lectura de PDF | Sin índice ni búsqueda, nombres ambiguos |
| V2: indexada | Los mismos 100 PDFs | Índice general, 10 índices de área, CSV, IDs estables | Documentos aún en PDF |
| V3: Markdown | 100 Markdown y 300 chunks | Índices, metadatos y FTS5/BM25 | No incluye embeddings ni búsqueda semántica |

Adicionalmente se incluyen **20 correos, 25 tickets y 10 seguimientos de proyectos**
sintéticos con referencias a procedimientos.

## Puesta en marcha

Python **3.12** es la versión comprobada y recomendada para local y Community Cloud.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Linux:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

Abrir la URL indicada en la terminal, normalmente `http://localhost:8501`.
El selector lateral cambia entre V1, V2 y V3. Las páginas de correos, tickets y
proyectos son comunes a todas las versiones.

## Flujo principal: descarga para ChatGPT desde Biblioteca

**El flujo preferente es trabajar con un ZIP local de una sola versión, no consultar
una API remota.** En la página **Documentación** de Streamlit, seleccione V1, V2 o V3
y pulse **Descargar esta biblioteca completa (ZIP)**. La descarga contiene:

- la estructura de carpetas y archivos de la versión elegida;
- `correos.json`, `tickets.json` y `proyectos.json`, idénticos en las tres versiones;
- **nunca** los índices privados de correspondencia o las respuestas de evaluación.

Suba el ZIP a la Biblioteca de ChatGPT y, en una conversación nueva, use
**Adjuntar > Añadir desde la Biblioteca** para seleccionarlo. Pida que se extraiga
el archivo y que se analice exclusivamente el contenido de ese paquete.
Si el entorno de ChatGPT incluye herramientas de ejecución/análisis de archivos,
puede trabajar sobre una extracción temporal. La Biblioteca guarda adjuntos reutilizables,
**no es un directorio de trabajo persistente** y no implica que ChatGPT descargue o
sincronice automáticamente datos desde Streamlit.

Para comparar V1, V2 y V3 con rigor, utilice conversaciones separadas y el mismo
cuestionario. No adjunte el repositorio completo ni `data/internal/` al agente evaluado.
En V1 no se incluye índice; en V2 se entregan los índices; en V3 se incluyen los
Markdown, `chunks.json` y el índice SQLite. No asuma que ChatGPT abre SQLite
sin una herramienta de ejecución habilitada.

## Acceso programático opcional (REST/MCP)

Streamlit sirve como interfaz humana. Para la integración con IA existen dos
adaptadores **de solo lectura**, ambos reutilizan los mismos archivos y reglas de
consulta. Hay que desplegar uno de ellos en un servidor alcanzable desde ChatGPT;
una dirección `localhost` de tu ordenador no es públicamente accesible.

### Alternativa A: REST/OpenAPI

Instalar `requirements-api.txt` en el entorno virtual para este adaptador.
La web de Streamlit no necesita FastAPI ni Uvicorn.

```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

- Especificación de herramientas: `http://localhost:8000/openapi.json`.
- Consola de pruebas: `http://localhost:8000/docs`.
- `GET /api/v1/browse?folder=`: carpetas V1.
- `GET /api/v1/read?path=...`: contenido de un PDF V1 descubierto.
- `GET /api/v2/areas`: áreas V2.
- `GET /api/v2/index/{area}`: metadatos de documentos del área.
- `GET /api/v2/document/{doc_id}`: texto del PDF y referencia.
- `GET /api/v3/search?query=...&limit=5`: chunks BM25 ordenados.
- `GET /api/v3/chunk/{chunk_id}`: fuente del fragmento.
- `GET /api/v3/document/{doc_id}`: Markdown con metadatos.
- `GET /api/examples/{kind}`: `correos`, `tickets`, `proyectos`.

Se puede emplear un servidor FastAPI públicamente desplegado como origen para
herramientas basadas en OpenAPI o crear un plugin/MCP sobre estos endpoints.
La disponibilidad de cada mecanismo en ChatGPT depende de la cuenta y del cliente.

### Alternativa B: MCP (adaptador opcional)

```bash
pip install -r requirements-mcp.txt
python mcp_server.py
```

Ofrece herramientas separadas para los tres experimentos y emplea transporte
Streamable HTTP. Normalmente publica `/mcp` en el servidor local; para enlazarlo
a ChatGPT deberá desplegarse con HTTPS y configurar la autenticación o las
restricciones de acceso de la plataforma correspondiente. **El adaptador MCP es
opcional y requiere pruebas de integración en el entorno final.**

### Clave API para REST

```bash
export LAB_API_KEY='una-clave-larga-y-aleatoria'
uvicorn api:app --host 0.0.0.0 --port 8000
curl -H 'Authorization: Bearer una-clave-larga-y-aleatoria' https://TU-SERVIDOR/api/catalog
```

El ejemplo anterior presupone que ya configuraste un servidor HTTPS. Si no se
establece `LAB_API_KEY`, los endpoints REST son públicos. No subir claves al
repositorio. El adaptador MCP debe protegerse independientemente al desplegarlo.

## Estructura

```text
streamlit_app.py           Interfaz humana
api.py                     API REST y OpenAPI
mcp_server.py              Adaptador opcional de herramientas MCP
lab/store.py               Capa única de lectura
tools/generate.py          Generador reproducible de corpus sintético
data/
  correos.json
  tickets.json
  proyectos.json
  v1_caotica/              Carpetas erráticas, PDFs, copias obsoletas
  v2_indexada/             ÍNDICE general, CSV e índices por área, PDFs
  v3_markdown/             Índices, Markdown, chunks.json y search.sqlite
  internal/                Correspondencia técnica para verificar paridad
tests/test_corpus.py
```

`data/internal/` contiene también un conjunto de 16 preguntas de evaluación
con respuesta esperada (`evaluacion.json`). Existe únicamente para **verificación y reproducibilidad**. No se
expone mediante la API. Un evaluador debe restringir el acceso del agente a las
herramientas correspondientes a la versión evaluada y **no** ofrecerle el
repositorio completo por GitHub: de lo contrario podría consultar el manifiesto
interno y arruinar la comparación.

## Regeneración y verificación

El corpus ya está generado; no se necesita ReportLab para ejecutar la web/API.
Para reconstruirlo determinísticamente:

```bash
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/generate.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check . --fix
.\.venv\Scripts\python.exe -m ruff format .
```

En Linux, sustituir `.\.venv\Scripts\python.exe` por `.venv/bin/python`.
El generador requiere ReportLab y sobrescribe las tres carpetas de datos.
Los tests verifican 100 procedimientos canónicos, la identidad binaria de los
PDF V1/V2, navegación segura, búsqueda, autenticación REST, aislamiento de los ZIP
y las páginas Streamlit con sus tres versiones documentales. GitHub Actions ejecuta
las comprobaciones en Windows y Linux, con Python 3.12.

Para repetir la comprobación en Linux desde Windows con Docker:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace,readonly" --workdir /workspace python:3.12-slim sh tools/check_linux.sh
```

El script crea un entorno virtual temporal dentro del contenedor, comprueba el
arranque con las dependencias mínimas de Cloud y después ejecuta todas las pruebas.
El proyecto se monta en modo de solo lectura.

## Prueba comparativa sugerida

1. Elegir una pregunta cuya respuesta aparezca en uno o varios documentos.
2. Ejecutar la misma pregunta con V1, V2 y V3 por separado.
3. Medir número de llamadas a herramientas, archivos leídos, tiempo, exactitud
   factual y correspondencia de la cita con el fragmento consultado.
4. Repetir para al menos 10 preguntas e incluir preguntas sin respuesta.

No se ha medido ninguna mejora de rendimiento: el repositorio aporta la
infraestructura experimental, no resultados del experimento.

## Despliegue gratuito en Streamlit Community Cloud

Repositorio: [DOKOS-TAYOS/laboratorio-documental-empresa](https://github.com/DOKOS-TAYOS/laboratorio-documental-empresa).

1. Acceder a [Streamlit Community Cloud](https://share.streamlit.io/) con GitHub.
2. Pulsar **Create app** y seleccionar el repositorio. Al ser privado, autorizar
   a Streamlit el acceso al repositorio si lo solicita.
3. Seleccionar la rama **main** y el archivo **streamlit_app.py**.
4. En **Advanced settings**, seleccionar **Python 3.12**.
5. No añadir secretos: esta demo no necesita claves API ni servicios externos.
6. Pulsar **Deploy** y esperar a que Streamlit muestre la dirección de la web.
7. Revisar quién puede ver la app en sus opciones de acceso antes de compartirla.

Cloud instala automáticamente `requirements.txt`. Los corpus PDF, Markdown y
SQLite ya están incluidos: **no ejecutar el generador durante el despliegue**.
No se necesita `packages.txt`, Docker, un servidor REST ni el adaptador MCP.
La configuración `.streamlit/config.toml` activa el modo sin ventana y desactiva
el envío de estadísticas de uso. Las descargas ZIP se guardan en caché, con un
máximo de tres versiones. La app lee los datos y no depende de guardar archivos
de usuarios en el disco temporal de Cloud.

Guía oficial: [despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
y [dependencias](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

El repositorio se mantiene privado porque incluye las respuestas del experimento
en `data/internal/`. Estas no se sirven desde la interfaz ni se incluyen en los ZIP.
Compartir la web o sus ZIP permite realizar la comparación sin entregar las respuestas.
Si se decide hacer público el repositorio, los participantes podrán consultar esas
respuestas y la comparación dejará de estar aislada.

REST y MCP se despliegan por separado cuando se necesita consulta remota; no forman
parte del alojamiento de esta web en Community Cloud.

## Procedencia y licencia

Todos los procedimientos, correos, tickets y seguimientos son contenido sintético
generado para este ejemplo. No proceden de empresas reales ni contienen datos reales.
No se redistribuyen manuales de terceros. Dependencias principales:
Streamlit (Apache-2.0), FastAPI (MIT), pypdf (BSD-3-Clause), ReportLab (BSD).
El código original del repositorio se distribuye bajo licencia MIT (archivo `LICENSE`).
