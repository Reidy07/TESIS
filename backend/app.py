from datetime import datetime
from hashlib import pbkdf2_hmac
from html import escape
import io
import json
import os
import sqlite3
from uuid import uuid4
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR)).resolve()
DB_PATH = DATA_DIR / "evaluador.db"
UPLOAD_DIR = DATA_DIR / "uploads"
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xlsx", "txt"}

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")
CORS(app)
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


QUESTIONS = [
    {"id": "N-01", "framework": "NIST", "group": "Govern", "criterion": "Roles y responsabilidades", "weight": 3, "question": "Se encuentran definidos, aprobados y comunicados los responsables de la ciberseguridad?", "evidence_expected": "Politica, organigrama, descripciones de puestos y asignaciones de responsabilidad.", "gap_text": "Las responsabilidades de seguridad son informales o desconocidas.", "recommendation": "Documentar los roles, obtener aprobacion y comunicarlos a las personas involucradas."},
    {"id": "N-02", "framework": "NIST", "group": "Govern", "criterion": "Direccion y politica", "weight": 3, "question": "La empresa posee lineamientos de ciberseguridad vinculados con sus objetivos y riesgos principales?", "evidence_expected": "Politica aprobada, objetivos, criterios de riesgo y actas de revision de la direccion.", "gap_text": "No existe una direccion comun para gestionar los riesgos de ciberseguridad.", "recommendation": "Aprobar una politica y definir objetivos, prioridades y criterios de riesgo."},
    {"id": "N-03", "framework": "NIST", "group": "Identify", "criterion": "Inventario de activos", "weight": 3, "question": "La empresa mantiene un inventario actualizado de sistemas, equipos, aplicaciones, datos y servicios criticos?", "evidence_expected": "Inventario, propietarios, clasificacion, fecha de actualizacion y registros de cambios.", "gap_text": "La empresa desconoce todos los activos que debe proteger.", "recommendation": "Elaborar un inventario, asignar propietarios y establecer revisiones periodicas."},
    {"id": "N-04", "framework": "NIST", "group": "Identify", "criterion": "Evaluacion de riesgos", "weight": 3, "question": "Se identifican y priorizan los riesgos que podrian afectar los activos y procesos criticos?", "evidence_expected": "Matriz de riesgos, analisis de amenazas, vulnerabilidades, impactos y prioridades.", "gap_text": "Los riesgos no se identifican o priorizan de manera consistente.", "recommendation": "Definir una metodologia sencilla de evaluacion y actualizar la matriz de riesgos."},
    {"id": "N-05", "framework": "NIST", "group": "Protect", "criterion": "Gestion de accesos", "weight": 3, "question": "Los accesos se crean, modifican, revisan y eliminan mediante un procedimiento controlado?", "evidence_expected": "Solicitudes, aprobaciones, listas de usuarios, revisiones y configuraciones de autenticacion.", "gap_text": "Permanecen accesos innecesarios, excesivos o no autorizados.", "recommendation": "Formalizar el alta, modificacion, revision y retiro de accesos."},
    {"id": "N-06", "framework": "NIST", "group": "Protect", "criterion": "Concienciacion y capacitacion", "weight": 2, "question": "El personal recibe formacion periodica sobre responsabilidades y amenazas de ciberseguridad?", "evidence_expected": "Plan de capacitacion, listas de asistencia, contenidos y resultados de evaluaciones.", "gap_text": "El personal desconoce amenazas y responsabilidades basicas.", "recommendation": "Crear un programa periodico de concienciacion adaptado a las funciones laborales."},
    {"id": "N-07", "framework": "NIST", "group": "Detect", "criterion": "Registro y monitoreo", "weight": 3, "question": "Se recopilan y revisan registros de sistemas para identificar eventos sospechosos?", "evidence_expected": "Registros, paneles de monitoreo, reglas de alerta y reportes de revision.", "gap_text": "Los eventos sospechosos podrian pasar inadvertidos.", "recommendation": "Centralizar registros relevantes y asignar responsables para su revision."},
    {"id": "N-08", "framework": "NIST", "group": "Detect", "criterion": "Analisis de anomalias", "weight": 2, "question": "Existen criterios para investigar y escalar comportamientos o eventos anomalos?", "evidence_expected": "Umbrales, tickets, registros de investigacion y procedimientos de escalamiento.", "gap_text": "Las alertas no se investigan ni escalan oportunamente.", "recommendation": "Definir umbrales, responsables y tiempos de escalamiento."},
    {"id": "N-09", "framework": "NIST", "group": "Respond", "criterion": "Plan de respuesta", "weight": 3, "question": "Existe un procedimiento documentado que establezca como actuar ante incidentes de seguridad?", "evidence_expected": "Plan, roles, contactos, formularios y procedimientos de notificacion.", "gap_text": "La respuesta ante incidentes depende de decisiones improvisadas.", "recommendation": "Documentar y probar un plan basico de respuesta a incidentes."},
    {"id": "N-10", "framework": "NIST", "group": "Respond", "criterion": "Analisis y comunicacion", "weight": 2, "question": "Los incidentes son analizados, comunicados y documentados para extraer lecciones de mejora?", "evidence_expected": "Informes de incidentes, comunicaciones, cronologias y registros de lecciones aprendidas.", "gap_text": "Los incidentes no generan aprendizaje organizacional.", "recommendation": "Registrar causas, comunicaciones, decisiones y lecciones aprendidas."},
    {"id": "N-11", "framework": "NIST", "group": "Recover", "criterion": "Copias y restauracion", "weight": 3, "question": "Se realizan copias de seguridad y pruebas periodicas de restauracion de la informacion critica?", "evidence_expected": "Politica, registros de respaldo, calendario y resultados de pruebas de restauracion.", "gap_text": "Las copias podrian ser inexistentes, incompletas o no recuperables.", "recommendation": "Definir frecuencia, proteccion y pruebas periodicas de restauracion."},
    {"id": "N-12", "framework": "NIST", "group": "Recover", "criterion": "Recuperacion y continuidad", "weight": 3, "question": "La empresa cuenta con procedimientos para recuperar servicios y actualizar sus planes despues de incidentes?", "evidence_expected": "Plan de recuperacion, prioridades, ejercicios, resultados y actualizaciones efectuadas.", "gap_text": "La recuperacion de servicios criticos no esta organizada.", "recommendation": "Establecer prioridades, responsabilidades y ejercicios de recuperacion."},
    {"id": "I-01", "framework": "ISO", "group": "Contexto y direccion", "criterion": "Contexto y partes interesadas", "weight": 2, "question": "La empresa identifica las condiciones internas, externas y necesidades que afectan la seguridad de la informacion?", "evidence_expected": "Analisis de contexto, partes interesadas, necesidades y requisitos aplicables.", "gap_text": "No se consideran adecuadamente el entorno ni las obligaciones aplicables.", "recommendation": "Documentar el contexto, las partes interesadas y sus principales necesidades."},
    {"id": "I-02", "framework": "ISO", "group": "Contexto y direccion", "criterion": "Definicion del alcance", "weight": 2, "question": "Se encuentran claramente definidos los procesos, ubicaciones, activos y servicios incluidos en la gestion de seguridad?", "evidence_expected": "Documento de alcance, limites, exclusiones justificadas y dependencias.", "gap_text": "El alcance de la gestion de seguridad es ambiguo.", "recommendation": "Delimitar procesos, ubicaciones, activos, interfaces y exclusiones justificadas."},
    {"id": "I-03", "framework": "ISO", "group": "Contexto y direccion", "criterion": "Politica de seguridad", "weight": 3, "question": "Existe una politica aprobada, comunicada y revisada periodicamente?", "evidence_expected": "Politica vigente, aprobacion de la direccion, comunicaciones y revisiones.", "gap_text": "La politica no existe, esta desactualizada o no ha sido comunicada.", "recommendation": "Aprobar, distribuir y revisar periodicamente la politica."},
    {"id": "I-04", "framework": "ISO", "group": "Contexto y direccion", "criterion": "Objetivos de seguridad", "weight": 2, "question": "Se han establecido objetivos medibles y responsables para mejorar la seguridad de la informacion?", "evidence_expected": "Objetivos, indicadores, responsables, plazos y registros de seguimiento.", "gap_text": "Las acciones de seguridad no se relacionan con objetivos medibles.", "recommendation": "Definir objetivos, indicadores, responsables y fechas de seguimiento."},
    {"id": "I-05", "framework": "ISO", "group": "Contexto y direccion", "criterion": "Roles organizacionales", "weight": 3, "question": "Las responsabilidades y autoridades relacionadas con la seguridad se encuentran formalmente asignadas?", "evidence_expected": "Organigrama, perfiles de puestos, asignaciones y aprobaciones.", "gap_text": "Existen funciones sin responsables claramente asignados.", "recommendation": "Formalizar autoridades, responsabilidades y mecanismos de rendicion de cuentas."},
    {"id": "I-06", "framework": "ISO", "group": "Gestion de riesgos", "criterion": "Metodologia de riesgos", "weight": 3, "question": "La empresa utiliza criterios consistentes para identificar, analizar y valorar riesgos de seguridad?", "evidence_expected": "Metodologia, escalas, criterios, matriz y resultados de evaluaciones.", "gap_text": "Las evaluaciones de riesgo producen resultados inconsistentes.", "recommendation": "Definir criterios uniformes de probabilidad, impacto y aceptacion."},
    {"id": "I-07", "framework": "ISO", "group": "Gestion de riesgos", "criterion": "Plan de tratamiento", "weight": 3, "question": "Se definen controles, responsables y plazos para tratar los riesgos identificados?", "evidence_expected": "Plan de tratamiento, responsables, aceptacion del riesgo residual y seguimiento.", "gap_text": "Los riesgos identificados permanecen sin tratamiento o seguimiento.", "recommendation": "Establecer controles, responsables, plazos y aceptacion del riesgo residual."},
    {"id": "I-08", "framework": "ISO", "group": "Apoyo y operacion", "criterion": "Preparacion del personal", "weight": 2, "question": "Las personas responsables poseen las competencias y conocimientos necesarios?", "evidence_expected": "Perfiles, certificados, plan formativo, asistencia y evaluaciones.", "gap_text": "El personal responsable carece de competencias o capacitacion suficiente.", "recommendation": "Identificar necesidades formativas y conservar evidencia de las competencias."},
    {"id": "I-09", "framework": "ISO", "group": "Apoyo y operacion", "criterion": "Gestion documental", "weight": 2, "question": "Las politicas, procedimientos y registros estan identificados, actualizados y protegidos contra modificaciones no autorizadas?", "evidence_expected": "Control de versiones, aprobaciones, repositorios y registros de cambios.", "gap_text": "Se utilizan documentos obsoletos o sin control de cambios.", "recommendation": "Implementar identificacion, aprobacion, versionado, acceso y conservacion documental."},
    {"id": "I-10", "framework": "ISO", "group": "Apoyo y operacion", "criterion": "Ejecucion controlada", "weight": 2, "question": "Las actividades de seguridad se realizan conforme a procedimientos y criterios previamente definidos?", "evidence_expected": "Procedimientos, listas de verificacion, registros de ejecucion y cambios autorizados.", "gap_text": "Los procesos de seguridad se ejecutan de manera irregular.", "recommendation": "Documentar procedimientos y conservar registros de su ejecucion."},
    {"id": "I-11", "framework": "ISO", "group": "Evaluacion y mejora", "criterion": "Indicadores", "weight": 2, "question": "La empresa utiliza metricas para verificar el desempeno de sus controles y procesos de seguridad?", "evidence_expected": "Indicadores, reportes, tendencias, responsables y revisiones periodicas.", "gap_text": "La empresa no puede medir si sus controles estan mejorando.", "recommendation": "Definir indicadores periodicos y responsables de analizarlos."},
    {"id": "I-12", "framework": "ISO", "group": "Evaluacion y mejora", "criterion": "Revision independiente", "weight": 3, "question": "Se realizan auditorias internas planificadas para evaluar la aplicacion de los criterios de seguridad?", "evidence_expected": "Programa, planes, listas de verificacion, hallazgos e informes.", "gap_text": "Las debilidades internas no son detectadas mediante revisiones planificadas.", "recommendation": "Crear un programa de auditoria basado en riesgos y documentar los hallazgos."},
    {"id": "I-13", "framework": "ISO", "group": "Evaluacion y mejora", "criterion": "Supervision directiva", "weight": 3, "question": "La direccion revisa periodicamente los resultados, riesgos, incidentes y oportunidades de mejora?", "evidence_expected": "Actas, informes ejecutivos, decisiones y seguimiento de compromisos.", "gap_text": "La direccion no participa suficientemente en la supervision de la seguridad.", "recommendation": "Programar revisiones directivas y documentar decisiones y compromisos."},
    {"id": "I-14", "framework": "ISO", "group": "Evaluacion y mejora", "criterion": "Acciones correctivas", "weight": 3, "question": "Las no conformidades y debilidades detectadas generan acciones correctivas verificables?", "evidence_expected": "Registro de hallazgos, analisis de causa, responsables, fechas y cierres.", "gap_text": "Los hallazgos se repiten porque no se eliminan sus causas.", "recommendation": "Aplicar analisis de causa, acciones correctivas y verificacion del cierre."},
    {"id": "I-15", "framework": "ISO", "group": "Activos y controles tecnologicos", "criterion": "Inventario y clasificacion", "weight": 3, "question": "Los activos de informacion se encuentran inventariados, clasificados y asignados a responsables?", "evidence_expected": "Inventario, clasificacion, propietarios y reglas de manejo.", "gap_text": "Los activos no poseen clasificacion ni responsable asignado.", "recommendation": "Inventariar, clasificar y establecer reglas de uso y proteccion."},
    {"id": "I-16", "framework": "ISO", "group": "Activos y controles tecnologicos", "criterion": "Ciclo de vida de accesos", "weight": 3, "question": "Los permisos de usuarios se autorizan, revisan y retiran oportunamente?", "evidence_expected": "Solicitudes, aprobaciones, listas, revisiones y registros de baja.", "gap_text": "Los accesos no corresponden con las funciones actuales de los usuarios.", "recommendation": "Aplicar minimo privilegio, revisiones periodicas y retiro oportuno."},
    {"id": "I-17", "framework": "ISO", "group": "Activos y controles tecnologicos", "criterion": "Respaldo de informacion", "weight": 3, "question": "Las copias de seguridad se realizan, protegen y prueban de acuerdo con las necesidades de la empresa?", "evidence_expected": "Politica, registros, medios protegidos y resultados de restauracion.", "gap_text": "Las copias no garantizan la recuperacion de informacion critica.", "recommendation": "Definir una politica de respaldo y realizar pruebas documentadas de restauracion."},
    {"id": "I-18", "framework": "ISO", "group": "Activos y controles tecnologicos", "criterion": "Supervision tecnologica", "weight": 3, "question": "Se generan, protegen y revisan registros de eventos relevantes?", "evidence_expected": "Logs, reglas de alerta, reportes de revision y retencion de registros.", "gap_text": "Los registros son insuficientes, modificables o no se revisan.", "recommendation": "Proteger los registros, establecer retencion y revisar alertas periodicamente."},
    {"id": "I-19", "framework": "ISO", "group": "Activos y controles tecnologicos", "criterion": "Gestion de vulnerabilidades", "weight": 3, "question": "Se identifican vulnerabilidades y se aplican actualizaciones de acuerdo con su criticidad?", "evidence_expected": "Escaneos, inventarios de versiones, tickets, parches y excepciones autorizadas.", "gap_text": "Los sistemas permanecen expuestos a vulnerabilidades conocidas.", "recommendation": "Mantener inventarios de versiones y aplicar parches segun criticidad."},
    {"id": "I-20", "framework": "ISO", "group": "Seguridad fisica y proveedores", "criterion": "Acceso fisico", "weight": 2, "question": "Las instalaciones y areas que contienen activos criticos cuentan con controles de acceso y proteccion?", "evidence_expected": "Listas de acceso, registros de visitantes, camaras y controles ambientales.", "gap_text": "Personas no autorizadas podrian acceder a instalaciones o equipos criticos.", "recommendation": "Implementar controles fisicos, registros de visitantes y revisiones de acceso."},
    {"id": "I-21", "framework": "ISO", "group": "Seguridad fisica y proveedores", "criterion": "Seguridad de terceros", "weight": 2, "question": "Los contratos y relaciones con proveedores incorporan requisitos de seguridad y seguimiento?", "evidence_expected": "Contratos, acuerdos, evaluaciones, obligaciones y revisiones de proveedores.", "gap_text": "Los proveedores podrian introducir riesgos no evaluados.", "recommendation": "Incorporar clausulas de seguridad y efectuar revisiones periodicas."},
    {"id": "I-22", "framework": "ISO", "group": "Incidentes y continuidad", "criterion": "Gestion de incidentes", "weight": 3, "question": "Los eventos de seguridad son reportados, clasificados, investigados y cerrados mediante un proceso formal?", "evidence_expected": "Procedimiento, tickets, informes, comunicaciones y lecciones aprendidas.", "gap_text": "Los incidentes se gestionan sin clasificacion, evidencia o seguimiento.", "recommendation": "Establecer un flujo formal de reporte, analisis, contencion y cierre."},
    {"id": "I-23", "framework": "ISO", "group": "Incidentes y continuidad", "criterion": "Continuidad y recuperacion", "weight": 3, "question": "La empresa mantiene y prueba medidas para continuar o recuperar operaciones criticas?", "evidence_expected": "Planes, prioridades, ejercicios, resultados y acciones de mejora.", "gap_text": "La empresa no puede recuperar oportunamente sus operaciones esenciales.", "recommendation": "Desarrollar, probar y actualizar planes de continuidad y recuperacion."},
]

SCORES = {"si": 1.0, "parcial": 0.5, "no": 0.0, "na": None}
NIST_GROUPS = ["Govern", "Identify", "Protect", "Detect", "Respond", "Recover"]
ISO_GROUPS = [
    "Contexto y direccion",
    "Gestion de riesgos",
    "Apoyo y operacion",
    "Evaluacion y mejora",
    "Activos y controles tecnologicos",
    "Seguridad fisica y proveedores",
    "Incidentes y continuidad",
]
DEFAULT_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "name": "Auditor TSI",
        "role": "Auditor",
    },
    {
        "username": "profesor",
        "password": "tesis2026",
        "name": "Revisor Academico",
        "role": "Consulta",
    },
    {
        "username": "empresa",
        "password": "empresa2026",
        "name": "Usuario Empresa Demo",
        "role": "Empresa",
    },
]


def hash_password(password):
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), b"evaluador-tsi", 120000)
    return digest.hex()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def require_auditor():
    if request.headers.get("X-User-Role") not in {"Auditor", "Administrador"}:
        return jsonify({"message": "Permiso denegado. Solo el auditor puede realizar esta accion."}), 403
    return None


def require_evaluation_writer():
    if request.headers.get("X-User-Role") not in {"Auditor", "Administrador", "Empresa"}:
        return jsonify({"message": "Permiso denegado. Solo perfiles autorizados pueden responder evaluaciones."}), 403
    return None


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                auditor TEXT NOT NULL,
                date TEXT NOT NULL,
                frameworks TEXT NOT NULL DEFAULT 'both',
                answers TEXT NOT NULL,
                evidence TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sector TEXT,
                employees INTEGER,
                auditor_responsible TEXT,
                contact TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS criteria (
                id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                group_name TEXT NOT NULL,
                criterion TEXT NOT NULL,
                question TEXT NOT NULL,
                evidence_expected TEXT NOT NULL,
                weight INTEGER NOT NULL,
                gap_text TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        for table, column, definition in [
            ("evaluations", "frameworks", "TEXT NOT NULL DEFAULT 'both'"),
            ("companies", "employees", "INTEGER"),
            ("companies", "auditor_responsible", "TEXT"),
        ]:
            existing_columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
            if column not in existing_columns:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        for user in DEFAULT_USERS:
            db.execute(
                """
                INSERT OR IGNORE INTO users (username, password_hash, name, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["username"],
                    hash_password(user["password"]),
                    user["name"],
                    user["role"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

        for index, question in enumerate(QUESTIONS, start=1):
            db.execute(
                """
                INSERT INTO criteria (
                    id, framework, group_name, criterion, question, evidence_expected,
                    weight, gap_text, recommendation, sort_order, active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                    framework = excluded.framework,
                    group_name = excluded.group_name,
                    criterion = excluded.criterion,
                    question = excluded.question,
                    evidence_expected = excluded.evidence_expected,
                    weight = excluded.weight,
                    gap_text = excluded.gap_text,
                    recommendation = excluded.recommendation,
                    sort_order = excluded.sort_order,
                    active = 1
                """,
                (
                    question["id"],
                    question["framework"],
                    question["group"],
                    question["criterion"],
                    question["question"],
                    question["evidence_expected"],
                    question["weight"],
                    question["gap_text"],
                    question["recommendation"],
                    index,
                ),
            )

        db.execute(
            """
            INSERT OR IGNORE INTO companies (name, sector, employees, auditor_responsible, contact, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Empresa Demo",
                "Servicios",
                35,
                "Jeissel",
                "contacto@empresa-demo.local",
                "Empresa de ejemplo para pruebas del prototipo.",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def selected_frameworks(frameworks):
    if frameworks == "NIST":
        return {"NIST"}
    if frameworks == "ISO":
        return {"ISO"}
    return {"NIST", "ISO"}


def criteria_from_db():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, framework, group_name, criterion, question, evidence_expected,
                   weight, gap_text, recommendation, sort_order
            FROM criteria
            WHERE active = 1
            ORDER BY sort_order ASC
            """
        ).fetchall()
    return [
        {
            "id": row["id"],
            "framework": row["framework"],
            "group": row["group_name"],
            "criterion": row["criterion"],
            "question": row["question"],
            "evidence_expected": row["evidence_expected"],
            "weight": row["weight"],
            "gap_text": row["gap_text"],
            "recommendation": row["recommendation"],
            "sort_order": row["sort_order"],
        }
        for row in rows
    ]


def has_evidence_record(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        note = (value.get("note") or "").strip()
        files = value.get("files") or []
        return bool(note or files)
    return False


def calculate_results(answers, frameworks="both"):
    allowed_frameworks = selected_frameworks(frameworks)
    group_totals = {"NIST": {}, "ISO": {}}
    group_max = {"NIST": {}, "ISO": {}}
    framework_totals = {"NIST": 0.0, "ISO": 0.0}
    framework_max = {"NIST": 0.0, "ISO": 0.0}
    response_distribution = {"si": 0, "parcial": 0, "no": 0, "na": 0}
    fulfilled_controls = 0
    applicable_controls = 0
    gaps = []

    by_id = {q["id"]: q for q in QUESTIONS}
    for question_id, answer in answers.items():
        question = by_id.get(question_id)
        if not question or question["framework"] not in allowed_frameworks:
            continue

        if answer in response_distribution:
            response_distribution[answer] += 1

        score = SCORES.get(answer)
        if score is None:
            continue

        weighted_score = score * question["weight"]
        group_key = question["group"]
        framework_label = question["framework"]

        group_totals[framework_label][group_key] = group_totals[framework_label].get(group_key, 0) + weighted_score
        group_max[framework_label][group_key] = group_max[framework_label].get(group_key, 0) + question["weight"]
        framework_totals[framework_label] += weighted_score
        framework_max[framework_label] += question["weight"]
        applicable_controls += 1
        if score == 1.0:
            fulfilled_controls += 1
        if score < 0.75:
            gaps.append(
                {
                    "id": question["id"],
                    "criterion": question["criterion"],
                    "question": question["question"],
                    "framework": framework_label,
                    "group": group_key,
                    "weight": question["weight"],
                    "gap": question["gap_text"],
                    "recommendation": question["recommendation"],
                    "severity": "Critica" if score == 0 else "Media",
                    "answer": answer,
                    "score": weighted_score,
                }
            )

    def percentages(framework, groups):
        values = {}
        for name in groups:
            maximum = group_max[framework].get(name, 0)
            values[name] = round((group_totals[framework].get(name, 0) / maximum) * 100) if maximum else 0
        return values

    nist_functions = percentages("NIST", NIST_GROUPS)
    iso_areas = percentages("ISO", ISO_GROUPS)

    nist = round((framework_totals["NIST"] / framework_max["NIST"]) * 100) if framework_max["NIST"] else 0
    iso = round((framework_totals["ISO"] / framework_max["ISO"]) * 100) if framework_max["ISO"] else 0
    selected_scores = [
        value
        for framework, value in (("NIST", nist), ("ISO", iso))
        if framework in allowed_frameworks and framework_max[framework]
    ]
    compliance = round(sum(selected_scores) / len(selected_scores)) if selected_scores else 0

    maturity = 1
    if compliance >= 85:
        maturity = 5
    elif compliance >= 70:
        maturity = 4
    elif compliance >= 50:
        maturity = 3
    elif compliance >= 30:
        maturity = 2

    return {
        "compliance": compliance,
        "nist": nist,
        "iso": iso,
        "maturity": maturity,
        "critical_gaps": len([gap for gap in gaps if gap["severity"] == "Critica"]),
        "fulfilled_controls": fulfilled_controls,
        "applicable_controls": applicable_controls,
        "pending_controls": len(gaps),
        "functions": nist_functions,
        "nist_functions": nist_functions,
        "iso_areas": iso_areas,
        "response_distribution": response_distribution,
        "points": {
            "nist_obtained": framework_totals["NIST"],
            "nist_applicable": framework_max["NIST"],
            "iso_obtained": framework_totals["ISO"],
            "iso_applicable": framework_max["ISO"],
        },
        "gaps": gaps,
    }


def score_level(value):
    if value >= 85:
        return "Solido"
    if value >= 70:
        return "Bueno"
    if value >= 50:
        return "En mejora"
    return "Critico"


def build_results_chart(results):
    data = [
        ("Alineacion NIST", results.get("nist", 0), colors.HexColor("#1b6b7a")),
        ("Cumplimiento ISO", results.get("iso", 0), colors.HexColor("#2f9b7c")),
    ]
    drawing = Drawing(490, 112)
    x_label = 10
    x_bar = 126
    bar_width = 265
    y = 78
    for label, value, color in data:
        drawing.add(String(x_label, y, label, fontSize=9, fillColor=colors.HexColor("#425b65")))
        drawing.add(Rect(x_bar, y - 5, bar_width, 13, fillColor=colors.HexColor("#e8f0ee"), strokeColor=None))
        drawing.add(Rect(x_bar, y - 5, bar_width * (value / 100), 13, fillColor=color, strokeColor=None))
        drawing.add(String(x_bar + bar_width + 12, y, f"{value}% - {score_level(value)}", fontSize=9, fillColor=colors.HexColor("#153b50")))
        y -= 34
    return drawing


def framework_label(value):
    if value == "NIST":
        return "NIST CSF 2.0"
    if value == "ISO":
        return "ISO/IEC 27001"
    return "NIST CSF 2.0 + ISO/IEC 27001"


def build_group_chart(title, values, palette):
    populated = [(name, value) for name, value in values.items()]
    height = max(72, 28 + (len(populated) * 25))
    drawing = Drawing(480, height)
    drawing.add(String(4, height - 16, title, fontSize=11, fillColor=colors.HexColor("#153b50")))
    if not populated:
        drawing.add(Rect(4, height - 55, 430, 28, fillColor=colors.HexColor("#f8fbfa"), strokeColor=colors.HexColor("#dbe5e2")))
        drawing.add(String(16, height - 43, "Sin datos para este referente.", fontSize=9, fillColor=colors.HexColor("#68808a")))
        return drawing

    y = height - 42
    label_width = 150
    bar_width = 228
    for index, (label, value) in enumerate(populated):
        color = colors.HexColor(palette[index % len(palette)])
        drawing.add(String(4, y, label[:32], fontSize=7.8, fillColor=colors.HexColor("#425b65")))
        drawing.add(Rect(label_width, y - 5, bar_width, 11, fillColor=colors.HexColor("#e8f0ee"), strokeColor=None))
        drawing.add(Rect(label_width, y - 5, bar_width * (value / 100), 11, fillColor=color, strokeColor=None))
        drawing.add(String(label_width + bar_width + 10, y, f"{value}%", fontSize=8.2, fillColor=colors.HexColor("#153b50")))
        y -= 25
    return drawing


def make_metric_cards(results):
    card_data = [
        ("Alineacion NIST", f"{results.get('nist', 0)}%", score_level(results.get("nist", 0)), "#1b6b7a"),
        ("Cumplimiento ISO", f"{results.get('iso', 0)}%", score_level(results.get("iso", 0)), "#2f9b7c"),
        ("Brechas criticas", str(results.get("critical_gaps", 0)), "Prioridad alta", "#c95f5f"),
        ("Sin evidencia", str(results.get("criteria_without_evidence", 0)), "Requiere soporte", "#d08b36"),
    ]
    row = []
    for label, value, caption, color in card_data:
        row.append(
            Table(
                [
                    [Paragraph(f"<font color='{color}'><b>{escape(value)}</b></font>", ParagraphStyle("metricValue", fontSize=21, leading=23, alignment=TA_CENTER))],
                    [Paragraph(escape(label), ParagraphStyle("metricLabel", fontSize=8.5, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#153b50")))],
                    [Paragraph(escape(caption), ParagraphStyle("metricCaption", fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#68808a")))],
                ],
                colWidths=[116],
                rowHeights=[24, 16, 16],
            )
        )
    cards = Table([row], colWidths=[120, 120, 120, 120], hAlign="LEFT")
    cards.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe5e2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe5e2")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fbfa")),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return cards


def make_section_title(text, styles):
    return Paragraph(escape(text), styles["SectionTitle"])


def standard_table_style(header_color="#153b50"):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#dbe5e2")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fbfa")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]
    )


def make_executive_summary(evaluation, results, styles):
    summary_text = (
        f"La evaluacion de {escape(evaluation['company'])} registra una alineacion NIST de "
        f"{results.get('nist', 0)}% y un cumplimiento ISO interno de {results.get('iso', 0)}%. "
        f"El nivel de madurez calculado es {results.get('maturity', 1)}, con "
        f"{results.get('pending_controls', 0)} brechas y {results.get('criteria_without_evidence', 0)} criterios sin evidencia."
    )
    action = "Mantener seguimiento periodico y actualizar evidencias."
    gaps = results.get("gaps") or []
    if gaps:
        first_gap = gaps[0]
        action = f"Priorizar {escape(first_gap.get('id', ''))} - {escape(first_gap.get('group', ''))}: {escape(first_gap.get('recommendation', ''))}"

    table = Table(
        [
            [
                Paragraph("<b>Lectura ejecutiva</b><br/>" + summary_text, styles["Body"]),
                Paragraph("<b>Accion sugerida</b><br/>" + action, styles["Body"]),
            ]
        ],
        colWidths=[240, 240],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#eef7f4")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#fff7eb")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#dbe5e2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe5e2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def evidence_rows(evidence):
    rows = [["Criterio", "Detalle registrado"]]
    for question_id, value in evidence.items():
        if isinstance(value, str) and value:
            rows.append([question_id, value])
        elif isinstance(value, dict):
            note = value.get("note")
            files = value.get("files") or []
            file_names = [item.get("file_name", "") for item in files if item.get("file_name")]
            details = ", ".join([part for part in [note, ", ".join(file_names)] if part])
            if details:
                rows.append([question_id, details])
    return rows


def draw_page_frame(canvas, doc):
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(colors.HexColor("#153b50"))
    canvas.rect(0, height - 40, width, 40, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#2f9b7c"))
    canvas.rect(0, height - 40, 118, 40, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(42, height - 23, "Evaluador automatico de ciberseguridad")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(width - 42, height - 23, "NIST CSF 2.0 / ISO IEC 27001")
    canvas.setStrokeColor(colors.HexColor("#dbe5e2"))
    canvas.setLineWidth(0.4)
    canvas.line(42, 34, width - 42, 34)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#68808a"))
    canvas.drawRightString(width - 42, 22, f"Pagina {doc.page}")
    canvas.restoreState()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"ok": False, "message": "Digite usuario y contrasena"}), 400

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user and user["password_hash"] == hash_password(password):
        return jsonify(
            {
                "ok": True,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "role": user["role"],
                },
            }
        )
    return jsonify({"ok": False, "message": "Credenciales invalidas"}), 401


@app.route("/api/questions")
def questions():
    return jsonify(criteria_from_db())


@app.route("/api/companies", methods=["GET"])
def list_companies():
    with get_db() as db:
        rows = db.execute("SELECT * FROM companies ORDER BY name ASC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/api/companies", methods=["POST"])
def create_company():
    permission_error = require_auditor()
    if permission_error:
        return permission_error

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"message": "El nombre de la empresa es requerido"}), 400

    try:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO companies (name, sector, employees, auditor_responsible, contact, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    (data.get("sector") or "").strip(),
                    int(data.get("employees") or 0) if str(data.get("employees") or "").strip() else None,
                    (data.get("auditor_responsible") or "").strip(),
                    (data.get("contact") or "").strip(),
                    (data.get("notes") or "").strip(),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            company_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"message": "La empresa ya esta registrada"}), 409

    return jsonify({"id": company_id, "name": name}), 201


@app.route("/api/evidence", methods=["POST"])
def upload_evidence():
    permission_error = require_evaluation_writer()
    if permission_error:
        return permission_error

    uploaded = request.files.get("file")
    question_id = request.form.get("question_id", "")
    if not uploaded or uploaded.filename == "":
        return jsonify({"message": "No se recibio ningun archivo"}), 400
    if not allowed_file(uploaded.filename):
        return jsonify({"message": "Tipo de archivo no permitido"}), 400

    original_name = secure_filename(uploaded.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid4().hex}.{extension}"
    stored_path = UPLOAD_DIR / stored_name
    uploaded.save(stored_path)

    return jsonify(
        {
            "question_id": question_id,
            "file_name": original_name,
            "stored_name": stored_name,
            "size": stored_path.stat().st_size,
            "url": f"/api/evidence/{stored_name}",
        }
    ), 201


@app.route("/api/evidence/<stored_name>")
def download_evidence(stored_name):
    safe_name = secure_filename(stored_name)
    path = UPLOAD_DIR / safe_name
    if not path.exists():
        return jsonify({"message": "Evidencia no encontrada"}), 404
    return send_file(path, as_attachment=True, download_name=safe_name)


@app.route("/api/evaluations", methods=["GET"])
def list_evaluations():
    with get_db() as db:
        rows = db.execute("SELECT * FROM evaluations ORDER BY id DESC").fetchall()
    evaluations = []
    for row in rows:
        item = dict(row)
        item["answers"] = json.loads(item["answers"])
        item["evidence"] = json.loads(item["evidence"])
        item["results"] = json.loads(item["results"])
        evaluations.append(item)
    return jsonify(evaluations)


@app.route("/api/evaluations", methods=["POST"])
def create_evaluation():
    permission_error = require_evaluation_writer()
    if permission_error:
        return permission_error

    data = request.get_json() or {}
    required = ["company", "auditor", "date", "answers"]
    if any(not data.get(field) for field in required):
        return jsonify({"message": "Faltan datos requeridos"}), 400

    evidence = data.get("evidence", {})
    frameworks = data.get("frameworks") or "both"
    allowed_frameworks = selected_frameworks(frameworks)
    selected_questions = {
        question["id"]: question
        for question in QUESTIONS
        if question["framework"] in allowed_frameworks and question["id"] in data["answers"]
    }
    missing_na_justification = [
        question_id
        for question_id, answer in data["answers"].items()
        if answer == "na"
        and question_id in selected_questions
        and not has_evidence_record(evidence.get(question_id))
    ]
    if missing_na_justification:
        return jsonify({"message": "Las respuestas 'No aplica' requieren justificacion."}), 400

    results = calculate_results(data["answers"], frameworks)
    results["criteria_without_evidence"] = len(
        [
            question_id
            for question_id, answer in data["answers"].items()
            if question_id in selected_questions
            and answer != "na"
            and not has_evidence_record(evidence.get(question_id))
        ]
    )
    results["opportunities"] = [
        {
            "id": gap["id"],
            "framework": gap["framework"],
            "group": gap["group"],
            "criterion": gap["criterion"],
            "recommendation": gap["recommendation"],
            "severity": gap["severity"],
        }
        for gap in results["gaps"][:5]
    ]
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO evaluations (company, auditor, date, frameworks, answers, evidence, results, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["company"],
                data["auditor"],
                data["date"],
                frameworks,
                json.dumps(data["answers"]),
                json.dumps(evidence),
                json.dumps(results),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        evaluation_id = cursor.lastrowid

    return jsonify({"id": evaluation_id, "results": results}), 201


@app.route("/api/evaluations/<int:evaluation_id>/report")
def report(evaluation_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)).fetchone()
    if not row:
        return jsonify({"message": "Evaluacion no encontrada"}), 404

    evaluation = dict(row)
    results = json.loads(evaluation["results"])
    evidence = json.loads(evaluation["evidence"])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=42, leftMargin=42, topMargin=54, bottomMargin=42)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "HeroSubtitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#d9e8e6"),
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#153b50"),
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "SmallMuted",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#68808a"),
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#17242b"),
        )
    )
    styles.add(
        ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#425b65"),
            backColor=colors.HexColor("#f8fbfa"),
            borderColor=colors.HexColor("#dbe5e2"),
            borderWidth=0.5,
            borderPadding=8,
            spaceAfter=12,
        )
    )

    hero = Table(
        [
            [
                Paragraph("Reporte ejecutivo de evaluacion", styles["ReportTitle"]),
                Paragraph(
                    f"<b>{escape(evaluation['company'])}</b><br/>{escape(evaluation['date'])}",
                    ParagraphStyle("HeroInfo", fontSize=9, leading=12, textColor=colors.white, alignment=TA_CENTER),
                ),
            ],
            [
                Paragraph(
                    "Evaluador automatico de ciberseguridad para PYMES basado en NIST CSF 2.0 e ISO/IEC 27001",
                    styles["HeroSubtitle"],
                ),
                Paragraph(
                    escape(framework_label(evaluation.get("frameworks", "both"))),
                    ParagraphStyle("HeroFramework", fontSize=8, leading=10, textColor=colors.HexColor("#d9e8e6"), alignment=TA_CENTER),
                ),
            ],
        ],
        colWidths=[350, 130],
        hAlign="LEFT",
    )
    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#153b50")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#1b6b7a")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#153b50")),
            ]
        )
    )

    story = [hero, Spacer(1, 12)]

    meta = [
        [
            Paragraph("<b>Empresa</b>", styles["Body"]),
            Paragraph(escape(evaluation["company"]), styles["Body"]),
            Paragraph("<b>Fecha</b>", styles["Body"]),
            Paragraph(escape(evaluation["date"]), styles["Body"]),
        ],
        [
            Paragraph("<b>Auditor</b>", styles["Body"]),
            Paragraph(escape(evaluation["auditor"]), styles["Body"]),
            Paragraph("<b>Referente</b>", styles["Body"]),
            Paragraph(escape(framework_label(evaluation.get("frameworks", "both"))), styles["Body"]),
        ],
    ]
    meta_table = Table(meta, hAlign="LEFT", colWidths=[72, 176, 72, 176])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fbfa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe5e2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5ecea")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.extend([
        meta_table,
        Spacer(1, 12),
        make_executive_summary(evaluation, results, styles),
        Spacer(1, 12),
        Paragraph(
            "Los resultados representan una evaluacion interna basada en los criterios seleccionados para este modelo "
            "y no constituyen una certificacion oficial de NIST o ISO/IEC 27001.",
            styles["Disclaimer"],
        ),
        make_metric_cards(results),
        Spacer(1, 14),
        make_section_title("Resultados separados por referente", styles),
        build_results_chart(results),
        Spacer(1, 14),
        make_section_title("Resultados por funcion y area", styles),
        build_group_chart("NIST CSF 2.0", results.get("nist_functions", results.get("functions", {})), ["#1b6b7a", "#2f9b7c", "#7c6fcb", "#d08b36"]),
        Spacer(1, 6),
        build_group_chart("ISO/IEC 27001", results.get("iso_areas", {}), ["#2f9b7c", "#1b6b7a", "#7c6fcb", "#d08b36", "#c95f5f"]),
    ])

    response_distribution = results.get("response_distribution", {})
    response_summary = [
        ["Respuesta", "Cantidad"],
        ["Cumple", str(response_distribution.get("si", 0))],
        ["Cumple parcialmente", str(response_distribution.get("parcial", 0))],
        ["No cumple", str(response_distribution.get("no", 0))],
        ["No aplica", str(response_distribution.get("na", 0))],
    ]
    response_table = Table(response_summary, hAlign="LEFT", colWidths=[210, 90])
    response_table.setStyle(standard_table_style())
    story.extend([Spacer(1, 10), make_section_title("Distribucion de respuestas", styles), response_table])

    evidence_data = evidence_rows(evidence)
    story.extend([Spacer(1, 12), make_section_title("Evidencias registradas", styles)])
    if len(evidence_data) > 1:
        evidence_table = Table(
            [[Paragraph(escape(str(cell)), styles["Body"]) for cell in row] for row in evidence_data],
            hAlign="LEFT",
            colWidths=[70, 420],
            repeatRows=1,
        )
        evidence_table.setStyle(standard_table_style())
        story.append(evidence_table)
    else:
        story.append(Paragraph("No se registraron evidencias para esta evaluacion.", styles["Body"]))

    story.extend([Spacer(1, 12), make_section_title("Brechas y recomendaciones", styles)])

    if results["gaps"]:
        gap_rows = [["Prioridad", "Criterio", "Brecha y recomendacion"]]
        for gap in results["gaps"]:
            details = f"<b>{escape(gap.get('question', ''))}</b><br/>"
            if gap.get("gap"):
                details += f"Brecha: {escape(gap['gap'])}<br/>"
            details += f"Recomendacion: {escape(gap.get('recommendation', ''))}"
            gap_rows.append(
                [
                    Paragraph(escape(gap.get("severity", "")), styles["Body"]),
                    Paragraph(f"{escape(gap.get('id', ''))}<br/>{escape(gap.get('framework', ''))} - {escape(gap.get('group', ''))}", styles["Body"]),
                    Paragraph(details, styles["Body"]),
                ]
            )
        gap_table = Table(gap_rows, hAlign="LEFT", colWidths=[62, 112, 316], repeatRows=1)
        gap_table.setStyle(standard_table_style("#1b6b7a"))
        story.append(gap_table)
    else:
        story.append(Paragraph("No se identificaron brechas relevantes en la evaluacion.", styles["Body"]))

    doc.build(story, onFirstPage=draw_page_frame, onLaterPages=draw_page_frame)
    buffer.seek(0)
    filename = f"reporte-evaluacion-{evaluation_id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@app.route("/")
def serve_frontend():
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return send_file(index_path)
    return jsonify({"message": "Frontend no compilado. Ejecute npm run build en frontend."}), 404


@app.route("/<path:path>")
def serve_spa(path):
    if path.startswith("api/"):
        return jsonify({"message": "Ruta API no encontrada."}), 404

    requested_path = FRONTEND_DIST / path
    if requested_path.exists() and requested_path.is_file():
        return send_file(requested_path)

    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return send_file(index_path)

    return jsonify({"message": "Frontend no compilado. Ejecute npm run build en frontend."}), 404


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
