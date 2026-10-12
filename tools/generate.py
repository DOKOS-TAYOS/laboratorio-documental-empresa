"""Deterministically generate all datasets and three equivalent documentation views.

Run: python tools/generate.py
Requires reportlab only at generation time.
"""

from __future__ import annotations

import csv
import json
import random
import re
import shutil
import sqlite3
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
V1 = DATA / "v1_caotica"
V2 = DATA / "v2_indexada"
V3 = DATA / "v3_markdown"
SEED = 20261012
rng = random.Random(SEED)

AREAS = {
    "operaciones": [
        "Apertura de turno",
        "Cierre de turno",
        "Transferencia de turno",
        "Parada controlada de línea",
        "Cambio de formato de producto",
        "Arranque de lote piloto",
        "Gestión de interrupción eléctrica",
        "Control de materiales en proceso",
        "Escalado de desviaciones operativas",
        "Reanudación tras parada prolongada",
    ],
    "calidad": [
        "Inspección de recepción",
        "Inspección visual de producto",
        "Control de equipos de medida",
        "Gestión de no conformidades",
        "Acciones correctivas y preventivas",
        "Auditoría interna",
        "Liberación de lote",
        "Trazabilidad de producto",
        "Gestión de reclamaciones de cliente",
        "Cambios de especificación",
    ],
    "mantenimiento": [
        "Mantenimiento preventivo semanal",
        "Atención a avería urgente",
        "Plan de lubricación",
        "Bloqueo y consignación de equipos",
        "Control de repuestos críticos",
        "Calibración de sensores",
        "Mantenimiento de cintas transportadoras",
        "Averías recurrentes",
        "Análisis de causa raíz de fallos",
        "Retorno seguro a servicio",
    ],
    "informatica": [
        "Alta de usuario corporativo",
        "Baja de usuario corporativo",
        "Restablecimiento de credenciales",
        "Clasificación de incidentes TI",
        "Restauración de copias de seguridad",
        "Revisión de permisos",
        "Instalación de software autorizado",
        "Aplicación de parches",
        "Respuesta a malware en equipos",
        "Conservación de registros técnicos",
    ],
    "seguridad": [
        "Notificación de accidente",
        "Evaluación de riesgos",
        "Uso de equipos de protección",
        "Evacuación de instalaciones",
        "Almacenamiento de productos químicos",
        "Permisos de trabajo especial",
        "Inspección de extintores",
        "Investigación de casi accidentes",
        "Control de visitas y contratistas",
        "Respuesta a derrames",
    ],
    "logistica": [
        "Recepción de mercancía",
        "Preparación de pedidos",
        "Expedición de pedidos",
        "Gestión de devoluciones",
        "Inventario cíclico",
        "Transporte urgente",
        "Etiquetado de palés",
        "Gestión de ubicaciones",
        "Cuarentena de material",
        "Previsión de necesidades logísticas",
    ],
    "compras": [
        "Solicitud de compra",
        "Homologación de proveedores",
        "Comparación de ofertas",
        "Emisión de orden de compra",
        "Discrepancias de facturación",
        "Renegociación de contratos",
        "Compra urgente",
        "Recepción de servicios",
        "Renovación de acuerdos",
        "Control de gastos menores",
    ],
    "personas": [
        "Incorporación de personal",
        "Salida de personal",
        "Registro de jornada",
        "Solicitud de vacaciones",
        "Formación obligatoria",
        "Evaluación de desempeño",
        "Cambio de puesto",
        "Mediación en conflictos",
        "Comunicación interna",
        "Acceso de personal externo",
    ],
    "proyectos": [
        "Inicio de proyecto",
        "Definición de hitos",
        "Registro de riesgos de proyecto",
        "Solicitudes de cambio",
        "Comité de seguimiento",
        "Informe semanal de avance",
        "Aceptación de entregables",
        "Cierre de proyecto",
        "Gestión de dependencias",
        "Control de presupuesto",
    ],
    "produccion": [
        "Planificación semanal de producción",
        "Medición de OEE",
        "Análisis de rechazo",
        "Control de cambio de línea",
        "Secuenciación de lotes",
        "Seguimiento de objetivos",
        "Gestión de desviaciones de turno",
        "Retrabajos autorizados",
        "Análisis de productividad",
        "Estimación de capacidad",
    ],
}

ROLES = {
    "operaciones": ("Supervisor de turno", "Jefatura de operaciones"),
    "calidad": ("Técnico de calidad", "Responsable de calidad"),
    "mantenimiento": ("Técnico de mantenimiento", "Jefatura de mantenimiento"),
    "informatica": ("Técnico de soporte TI", "Responsable de TI"),
    "seguridad": ("Técnico de prevención", "Responsable de seguridad"),
    "logistica": ("Coordinador de almacén", "Responsable de logística"),
    "compras": ("Comprador", "Responsable de compras"),
    "personas": ("Técnico de personas", "Responsable de personas"),
    "proyectos": ("Coordinador de proyecto", "Dirección de proyectos"),
    "produccion": ("Planificador de producción", "Dirección de producción"),
}

ACTIONS = {
    "operaciones": [
        "Revisar la hoja del turno y los equipos asignados",
        "Contrastar las órdenes abiertas con la planificación del día",
        "Registrar el estado inicial de la línea y sus parámetros",
        "Coordinar la intervención con el equipo del turno",
        "Validar que los controles operativos estén completos",
        "Registrar desvíos y responsables de resolución",
    ],
    "calidad": [
        "Identificar muestra, lote y especificación aplicable",
        "Verificar el estado de calibración del instrumento",
        "Realizar la inspección conforme al plan de muestreo",
        "Registrar evidencias y resultados observables",
        "Bloquear material si el criterio de aceptación falla",
        "Solicitar verificación independiente antes de liberar",
    ],
    "mantenimiento": [
        "Identificar el activo y su criticidad",
        "Revisar historial y órdenes de trabajo pendientes",
        "Asegurar consignación y permisos que correspondan",
        "Ejecutar la comprobación técnica y registrar medidas",
        "Realizar la prueba funcional con personal autorizado",
        "Cerrar la intervención y comunicar las restricciones",
    ],
    "informatica": [
        "Validar identidad y autorización de la solicitud",
        "Registrar el identificador del activo o cuenta",
        "Aplicar la operación en el entorno correspondiente",
        "Comprobar el principio de mínimo privilegio",
        "Probar el resultado sin divulgar credenciales",
        "Cerrar el ticket con evidencia no sensible",
    ],
    "seguridad": [
        "Delimitar el área y proteger a las personas",
        "Consultar evaluación de riesgos y permisos",
        "Comunicar la actuación al responsable de prevención",
        "Aplicar las barreras o controles establecidos",
        "Recopilar evidencias y registrar observaciones",
        "Verificar el cierre de las medidas preventivas",
    ],
    "logistica": [
        "Identificar pedido, material y destino",
        "Comprobar etiquetas, cantidades y lote",
        "Validar condiciones de manipulación y almacenamiento",
        "Registrar movimiento en el inventario",
        "Resolver discrepancias antes de liberar el material",
        "Confirmar entrega y conservar justificantes",
    ],
    "compras": [
        "Comprobar necesidad y centro de coste",
        "Verificar proveedor habilitado y condiciones pactadas",
        "Obtener aprobación dentro del umbral aplicable",
        "Formalizar la transacción y conservar evidencia",
        "Verificar recepción contra pedido",
        "Registrar cierre y eventuales discrepancias",
    ],
    "personas": [
        "Validar solicitud y autorización de la jefatura",
        "Comprobar requisitos y documentación necesaria",
        "Coordinar fechas con las partes involucradas",
        "Registrar el movimiento respetando confidencialidad",
        "Notificar solo a destinatarios autorizados",
        "Confirmar cierre y actualizar registro de seguimiento",
    ],
    "proyectos": [
        "Definir alcance, resultado esperado y responsable",
        "Actualizar hitos, dependencias y riesgos",
        "Recoger evidencias de avance verificables",
        "Contrastar desviaciones con la línea base",
        "Acordar acciones, fechas y criterios de aceptación",
        "Publicar el estado en el registro del proyecto",
    ],
    "produccion": [
        "Revisar orden de fabricación y prioridades",
        "Comprobar disponibilidad de máquinas y materiales",
        "Registrar la referencia de lote y capacidad prevista",
        "Monitorizar indicadores durante la ejecución",
        "Documentar causas de parada o rechazos",
        "Validar cierre de turno con los datos de producción",
    ],
}


def slug(s: str) -> str:
    import unicodedata

    s = "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def docs() -> list[dict]:
    records = []
    for area_idx, (area, titles) in enumerate(AREAS.items()):
        for j, title in enumerate(titles, 1):
            k = area_idx * 10 + j
            doc_id = f"PROC-{k:03d}"
            owner, approver = ROLES[area]
            sibling = f"PROC-{area_idx * 10 + (j % 10) + 1:03d}"
            sec = [
                (
                    "Objetivo",
                    f"Establecer la secuencia verificable para {title.lower()} en la empresa ficticia Nexo Industrial. Este procedimiento evita decisiones informales, define responsables y permite auditar cuándo se completó cada actuación.",
                ),
                (
                    "Ámbito de aplicación",
                    f"Se aplica al área de {area} en los centros Norte y Sur. Debe utilizarse en operaciones ordinarias y en las actuaciones extraordinarias relacionadas con {title.lower()}. No reemplaza requisitos legales ni autorizaciones específicas.",
                ),
                (
                    "Responsabilidades",
                    f"La ejecución corresponde al rol «{owner}». La aprobación de excepciones corresponde a «{approver}». El equipo debe comunicar bloqueos antes de continuar. Toda aprobación queda registrada con fecha, persona y motivo.",
                ),
                (
                    "Condiciones de inicio",
                    f"Abrir un registro {area.upper()}-{k:03d} indicando solicitante, fecha, activo o expediente y prioridad. Confirmar que el objetivo de «{title}» sea relevante y que la información de partida está disponible. Para prioridad crítica, avisar al responsable en un máximo de {10 + (j % 4) * 5} minutos.",
                ),
                (
                    "Procedimiento",
                    "\n".join(
                        f"{i + 1}. {step}. Cuando exista una discrepancia en «{title.lower()}», anotar el dato observado y la decisión tomada."
                        for i, step in enumerate(ACTIONS[area])
                    ),
                ),
                (
                    "Criterios de aceptación",
                    f"La actuación se considera completa si los seis pasos han quedado documentados, el responsable ha confirmado las evidencias y no existen acciones críticas abiertas. Tolerancia operativa interna de referencia: {2 + (j % 4)} unidades de desviación en el indicador local; es un parámetro sintético para la práctica.",
                ),
                (
                    "Gestión de excepciones",
                    f"Ante ausencia de evidencia, detener la liberación o el cierre y elevar a {approver}. Las decisiones extraordinarias requieren justificación escrita y revisión dentro de {1 + (j % 3)} días laborables. No alterar registros originales.",
                ),
                (
                    "Registros y trazabilidad",
                    f"Conservar acta, comprobante o ticket asociado bajo el código {doc_id}; registrar número de lote o proyecto, fecha y responsable. Vincular incidencias a su ticket y compartir únicamente con personas autorizadas.",
                ),
                (
                    "Documentos relacionados",
                    f"Consultar {sibling} del área {area} para la siguiente fase o comprobación relacionada. En caso de incompatibilidad, prevalece la revisión aprobada más reciente.",
                ),
                (
                    "Control documental",
                    f"Versión 1.{j % 4}, estado vigente a efectos de esta simulación. Revisión prevista: 2027-{(j % 12) + 1:02d}-15. Todos los datos y procesos de Nexo Industrial son ficticios.",
                ),
            ]
            records.append(
                dict(
                    id=doc_id,
                    area=area,
                    title=title,
                    owner=owner,
                    approver=approver,
                    version=f"1.{j % 4}",
                    related=sibling,
                    sections=sec,
                    summary=f"Procedimiento para {title.lower()}: inicio, responsables, pasos, aceptación, excepciones y registros.",
                )
            )
    return records


def plaintext(doc: dict) -> str:
    return "\n\n".join(f"{h}\n{body}" for h, body in doc["sections"])


def render_pdf(doc: dict, target: Path, outdated: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    style = getSampleStyleSheet()
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if font_path.exists() and "DV" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DV", str(font_path)))
    font = "DV" if "DV" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    normal = ParagraphStyle(
        "normal2",
        parent=style["BodyText"],
        fontName=font,
        fontSize=8.7,
        leading=13,
        spaceAfter=5,
    )
    hd = ParagraphStyle(
        "h2",
        parent=normal,
        fontSize=10.7,
        leading=14,
        spaceBefore=10,
        spaceAfter=3,
        keepWithNext=True,
        textColor=colors.HexColor("#114366"),
    )
    title = ParagraphStyle(
        "title2",
        parent=normal,
        fontSize=15.5,
        leading=21,
        spaceAfter=10,
        textColor=colors.HexColor("#122b3a"),
    )
    small = ParagraphStyle("small2", parent=normal, fontSize=8.2, textColor=colors.grey)
    story = [
        Paragraph(f"{doc['id']} · {doc['title']}", title),
        Paragraph(
            f"NEXO INDUSTRIAL · {doc['area'].upper()} · Revisión {'0.8 (obsoleta)' if outdated else doc['version']} · SIMULACIÓN",
            small,
        ),
        Spacer(1, 8),
    ]
    from xml.sax.saxutils import escape

    for heading, content in doc["sections"]:
        story.append(Paragraph(escape(heading), hd))
        for line in content.split("\n"):
            story.append(Paragraph(escape(line), normal))
    pdf = SimpleDocTemplate(
        str(target),
        pagesize=(595.27, 841.89),
        rightMargin=48,
        leftMargin=48,
        topMargin=46,
        bottomMargin=48,
        title=f"{doc['id']} {doc['title']}",
        author="Nexo Industrial - ejemplo sintético",
        invariant=1,
    )
    pdf.build(story)


def write_csv(path: Path, data: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{k: d[k] for k in cols} for d in data])


def markdown(doc: dict) -> str:
    yaml = "\n".join(
        [
            "---",
            f"id: {doc['id']}",
            f"area: {doc['area']}",
            f'titulo: "{doc["title"]}"',
            f'version: "{doc["version"]}"',
            f'responsable: "{doc["owner"]}"',
            f"documento_relacionado: {doc['related']}",
            "estado: vigente",
            "sintetico: true",
            "---",
            "",
        ]
    )
    sections = "\n\n".join(f"## {h}\n\n{b}" for h, b in doc["sections"])
    return f"{yaml}\n# {doc['id']}: {doc['title']}\n\n{sections}\n"


def make_chunks(doc: dict) -> list[dict]:
    chunks = []
    bucket = []
    headings = []
    words = 0
    for heading, body in doc["sections"]:
        count = len(body.split())
        if bucket and words + count > 230:
            chunks.append((headings[:], "\n\n".join(bucket)))
            bucket = []
            headings = []
            words = 0
        headings.append(heading)
        bucket.append(f"## {heading}\n{body}")
        words += count
    if bucket:
        chunks.append((headings[:], "\n\n".join(bucket)))
    return [
        dict(
            chunk_id=f"{doc['id']}-C{idx:02d}",
            document_id=doc["id"],
            area=doc["area"],
            title=doc["title"],
            ordinal=idx,
            headings=heads,
            text=body,
            source=f"{doc['area']}/{doc['id']}.md",
        )
        for idx, (heads, body) in enumerate(chunks, 1)
    ]


def make_examples(records: list[dict]) -> None:
    emails = []
    ticket_types = [
        "Incidencia de sensor",
        "Fallo de acceso",
        "Retraso de material",
        "Desviación de calidad",
        "Parada no planificada",
        "Reclamación de cliente",
        "Solicitud de cambio",
        "Bloqueo de compra",
    ]
    projects = []
    tickets = []
    for i in range(1, 26):
        doc = records[(i * 7) % len(records)]
        status = ["Abierto", "En investigación", "Resuelto", "Pendiente de aprobación"][
            i % 4
        ]
        priority = ["Baja", "Media", "Alta", "Crítica"][i % 4]
        tickets.append(
            dict(
                id=f"INC-{i:04d}",
                asunto=f"{ticket_types[i % len(ticket_types)]} en centro {'Norte' if i % 2 else 'Sur'}",
                prioridad=priority,
                estado=status,
                area=doc["area"],
                procedimiento=doc["id"],
                descripcion=f"Se observa una anomalía sintética ligada a {doc['title'].lower()}. Registro recibido en turno {i % 3 + 1}.",
                actuacion=f"Aplicar {doc['id']}, conservar evidencia y escalar a {doc['approver']} cuando corresponda.",
            )
        )
    for i in range(1, 21):
        doc = records[(i * 11) % len(records)]
        emails.append(
            dict(
                id=f"MAIL-{i:03d}",
                fecha=f"2026-09-{(i % 28) + 1:02d}",
                remitente=f"{['soporte', 'calidad', 'operaciones', 'proyectos'][i % 4]}@nexo.example",
                destinatario=f"equipo-{doc['area']}@nexo.example",
                asunto=f"Seguimiento {doc['id']}: {doc['title']}",
                cuerpo=f"Buenos días:\n\nSe solicita confirmar el estado de «{doc['title']}» según {doc['id']}. "
                f"El equipo debe remitir el registro firmado y las desviaciones abiertas antes del cierre del viernes. "
                f"Si existe bloqueo, comunicarlo a {doc['approver']}.\n\nSaludos,\nCoordinación interna",
            )
        )
    for i in range(1, 11):
        doc = records[80 + (i - 1)]
        projects.append(
            dict(
                id=f"PRJ-{i:03d}",
                nombre=f"Proyecto {i:02d}: mejora {doc['title'].lower()}",
                avance_porcentaje=min(100, 20 + 8 * i),
                fase=["Planificación", "Ejecución", "Validación", "Cierre"][i % 4],
                responsable="Oficina de proyectos",
                fecha_objetivo=f"2027-{i:02d}-25",
                riesgo=f"Dependencia pendiente de {records[(i * 6) % 100]['area']}",
                ultima_actualizacion=f"2026-10-{(i % 10) + 1:02d}",
                procedimiento=doc["id"],
            )
        )
    for label, items in [
        ("correos", emails),
        ("tickets", tickets),
        ("proyectos", projects),
    ]:
        (DATA / f"{label}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main() -> None:
    for p in [V1, V2, V3]:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True)
    records = docs()
    rand_dirs = [
        ("Documentos", "Viejos", "Otros"),
        ("General", "2023", "Pendiente"),
        ("Procesos", "Miscelanea"),
        ("Cosas", "Revision", "Final"),
        ("Documentacion", "Nueva"),
        ("TEMP", "Varios"),
        ("Backup", "Ultima-version"),
        ("Areas", "Sin-clasificar"),
        ("Historico", "Aprobado"),
        ("Equipo", "Carpetas", "Copia"),
    ]
    bad_names = [
        "final",
        "nuevo",
        "documento",
        "proced",
        "copia",
        "revisto",
        "v_final",
        "scan",
        "manual",
        "actualizado",
    ]
    paths = []
    chunks = []
    mapping = []
    for i, doc in enumerate(records):
        # Different depths, no coherent area hierarchy; stable but deliberately hard to discover.
        base = rand_dirs[(i * 17 + 3) % len(rand_dirs)]
        if i % 3 == 0:
            base = base + (f"Lote_{(i * 7) % 9}",)
        fn = f"{bad_names[i % len(bad_names)]}_{i % 13:02d}_{i:03d}.pdf"
        rel = Path(*base) / fn
        output = V1 / rel
        render_pdf(doc, output)
        doc["v1_path"] = str(rel).replace("\\", "/")
        target = V2 / doc["area"] / f"{doc['id']}_{slug(doc['title'])}.pdf"
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(output, target)
        doc["v2_path"] = str(target.relative_to(V2))
        md_path = V3 / doc["area"] / f"{doc['id']}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown(doc), encoding="utf-8")
        doc["v3_path"] = str(md_path.relative_to(V3))
        chunks.extend(make_chunks(doc))
        paths.append(dict(id=doc["id"], path=doc["v1_path"]))
        mapping.append({k: v for k, v in doc.items() if k != "sections"})
    # Include eight obsolete duplicates as traps in V1; no corresponding canonical docs in V2/V3.
    for i in range(8):
        doc = records[(i * 13 + 1) % 100]
        render_pdf(
            doc,
            V1 / "Backup" / "Ultima-version" / f"copia_actual_{i:02d}.pdf",
            outdated=True,
        )
    for area in AREAS:
        subset = [doc for doc in records if doc["area"] == area]
        cols = ["id", "title", "summary", "version", "owner", "related", "v2_path"]
        write_csv(V2 / area / "indice.csv", subset, cols)
        text = [
            "# Índice: " + area,
            "",
            f"Área: **{area}**. Documentos vigentes: **{len(subset)}**.",
            "",
            "| ID | Documento | Resumen |",
            "|---|---|---|",
        ]
        text.extend(
            f"| {doc['id']} | [{doc['title']}]({doc['id']}_{slug(doc['title'])}.pdf) | {doc['summary']} |"
            for doc in subset
        )
        (V2 / area / "INDICE.md").write_text("\n".join(text) + "\n", encoding="utf-8")
        summary = ["# Índice Markdown: " + area, "", "| ID | Documento |", "|---|---|"]
        summary.extend(
            f"| {doc['id']} | [{doc['title']}]({doc['id']}.md) |" for doc in subset
        )
        (V3 / area / "INDICE.md").write_text(
            "\n".join(summary) + "\n", encoding="utf-8"
        )
    write_csv(
        V2 / "indice_documentos.csv",
        records,
        ["id", "area", "title", "summary", "version", "owner", "related", "v2_path"],
    )
    (V2 / "INDICE_GENERAL.md").write_text(
        "# Índice general de documentación\n\n"
        + "La IA debe empezar aquí, identificar el área y abrir su índice antes de consultar el PDF.\n\n"
        + "\n".join(
            f"- [{area}]({area}/INDICE.md): {len(AREAS[area])} procedimientos."
            for area in AREAS
        )
        + "\n",
        encoding="utf-8",
    )
    (V3 / "INDICE_GENERAL.md").write_text(
        "# Índice general Markdown\n\n"
        + "\n".join(
            f"- [{area}]({area}/INDICE.md): {len(AREAS[area])} procedimientos."
            for area in AREAS
        )
        + "\n",
        encoding="utf-8",
    )
    (V3 / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # SQLite search is generated locally, not required as the source of truth.
    db = V3 / "search.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        'CREATE VIRTUAL TABLE chunks USING fts5(chunk_id UNINDEXED, document_id UNINDEXED, area UNINDEXED, title, body, tokenize="unicode61 remove_diacritics 2")'
    )
    con.executemany(
        "INSERT INTO chunks(chunk_id,document_id,area,title,body) VALUES(?,?,?,?,?)",
        [
            (c["chunk_id"], c["document_id"], c["area"], c["title"], c["text"])
            for c in chunks
        ],
    )
    con.commit()
    con.close()
    (DATA / "internal").mkdir(exist_ok=True)
    (DATA / "internal" / "correspondencias.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    make_examples(records)
    # Evaluation answers stay outside the version-specific tool surfaces.
    chosen = [4, 12, 19, 25, 34, 39, 43, 54, 66, 70, 76, 84, 90, 96, 99]
    benchmark = []
    for idx in chosen:
        d = records[idx]
        benchmark.append(
            {
                "question_id": f"Q-{len(benchmark) + 1:02d}",
                "question": f"En el procedimiento de «{d['title']}», ¿quién debe aprobar las excepciones y cuál es su identificador?",
                "expected_doc_id": d["id"],
                "expected_approver": d["approver"],
                "require_source": True,
            }
        )
    benchmark.append(
        {
            "question_id": "Q-16",
            "question": "¿Cuál es la facturación real de Nexo Industrial en 2025?",
            "expected_doc_id": None,
            "expected_answer": None,
            "require_source": True,
            "note": "La información no aparece: respuesta correcta, declarar ausencia de evidencia.",
        }
    )
    (DATA / "internal" / "evaluacion.json").write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "inventario.json").write_text(
        json.dumps(
            dict(
                documentos_canonicos=len(records),
                pdf_v1=len(records) + 8,
                pdf_v2=len(records),
                markdown_v3=len(records),
                chunks_v3=len(chunks),
                correos=20,
                tickets=25,
                proyectos=10,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Generated", len(records), "procedures and", len(chunks), "chunks")


if __name__ == "__main__":
    main()
