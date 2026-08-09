import io

from app import app, init_db


init_db()
AUDITOR_HEADERS = {"X-User-Role": "Auditor"}
REVIEWER_HEADERS = {"X-User-Role": "Consulta"}

payload = {
    "company": "Empresa Demo",
    "auditor": "Jeissel",
    "date": "2026-08-06",
    "frameworks": "both",
    "answers": {
        "N-01": "si",
        "N-02": "parcial",
        "N-03": "si",
        "N-04": "parcial",
        "N-05": "si",
        "N-06": "parcial",
        "N-07": "parcial",
        "N-08": "no",
        "N-09": "si",
        "N-10": "parcial",
        "N-11": "si",
        "N-12": "parcial",
        "I-01": "si",
        "I-02": "si",
        "I-03": "parcial",
        "I-04": "parcial",
        "I-05": "si",
        "I-06": "parcial",
        "I-07": "no",
        "I-08": "si",
        "I-09": "parcial",
        "I-10": "si",
        "I-11": "parcial",
        "I-12": "no",
        "I-13": "parcial",
        "I-14": "parcial",
        "I-15": "si",
        "I-16": "parcial",
        "I-17": "si",
        "I-18": "parcial",
        "I-19": "no",
        "I-20": "si",
        "I-21": "parcial",
        "I-22": "no",
        "I-23": "parcial",
    },
    "evidence": {
        "N-01": "Politica de seguridad.pdf",
        "N-03": "Inventario de activos.xlsx",
        "I-18": "Captura monitoreo.png",
    },
}

with app.test_client() as client:
    questions = client.get("/api/questions")
    assert questions.status_code == 200
    assert len(questions.get_json()) == 35
    companies = client.get("/api/companies")
    assert companies.status_code == 200
    created_company = client.post(
        "/api/companies",
        headers=AUDITOR_HEADERS,
        json={
            "name": "Empresa Smoke Test",
            "sector": "Servicios",
            "employees": 35,
            "auditor_responsible": "Maria Perez",
            "contact": "qa@example.local",
            "notes": "Registro creado por prueba automatica.",
        },
    )
    assert created_company.status_code in (201, 409)
    evidence_upload = client.post(
        "/api/evidence",
        headers=AUDITOR_HEADERS,
        data={
            "question_id": "N-01",
            "file": (io.BytesIO(b"evidencia de prueba"), "evidencia.txt"),
        },
        content_type="multipart/form-data",
    )
    assert evidence_upload.status_code == 201
    evidence_file = evidence_upload.get_json()
    payload["evidence"]["N-01"] = {"note": "Politica revisada", "files": [evidence_file]}
    denied = client.post("/api/evaluations", headers=REVIEWER_HEADERS, json=payload)
    assert denied.status_code == 403
    created = client.post("/api/evaluations", headers=AUDITOR_HEADERS, json=payload)
    assert created.status_code == 201
    evaluation_id = created.get_json()["id"]
    report = client.get(f"/api/evaluations/{evaluation_id}/report")
    assert report.status_code == 200
    assert report.mimetype == "application/pdf"
    print(f"Smoke test OK. Evaluacion #{evaluation_id} creada y PDF generado.")
