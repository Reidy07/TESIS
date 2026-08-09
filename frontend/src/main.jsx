import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  Activity,
  AlertTriangle,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Download,
  Eye,
  EyeOff,
  FileText,
  Gauge,
  LockKeyhole,
  LogOut,
  Plus,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

const API = "http://127.0.0.1:5000/api";
const answerLabels = {
  si: "Cumple",
  parcial: "Cumple parcialmente",
  no: "No cumple",
  na: "No aplica",
};
const moduleObjectives = {
  Govern: "Evaluar como la empresa gestiona la ciberseguridad.",
  Identify: "Identificar activos, responsables y riesgos principales.",
  Protect: "Verificar controles preventivos para proteger informacion y sistemas.",
  Detect: "Evaluar la capacidad de deteccion y monitoreo de eventos.",
  Respond: "Revisar la preparacion para responder ante incidentes.",
  Recover: "Medir la capacidad de recuperacion y mejora posterior a incidentes.",
  "Contexto y direccion": "Revisar alcance, politica, objetivos y responsabilidades de seguridad.",
  "Gestion de riesgos": "Evaluar la identificacion, valoracion y tratamiento de riesgos.",
  "Apoyo y operacion": "Comprobar competencia, documentacion y ejecucion operativa.",
  "Evaluacion y mejora": "Medir seguimiento, auditoria interna, revision y mejora continua.",
  "Activos y controles tecnologicos": "Verificar controles practicos sobre activos, accesos, respaldos y registros.",
  "Seguridad fisica y proveedores": "Evaluar proteccion fisica y requisitos de seguridad para terceros.",
  "Incidentes y continuidad": "Revisar gestion de incidentes y capacidad de continuidad.",
};
const chartPalette = ["#1b6b7a", "#2f9b7c", "#7c6fcb", "#d08b36", "#c95f5f", "#4f7ea8"];
const responsePalette = {
  si: "#2f9b7c",
  parcial: "#d08b36",
  no: "#c95f5f",
  na: "#8c9aa1",
};

function frameworkLabel(value) {
  if (value === "NIST") return "NIST CSF 2.0";
  if (value === "ISO") return "ISO/IEC 27001";
  return "NIST CSF 2.0 + ISO/IEC 27001";
}

function formatEvaluationResult(item) {
  const result = item?.results || {};
  if (item?.frameworks === "NIST") return `NIST ${result.nist || 0}%`;
  if (item?.frameworks === "ISO") return `ISO ${result.iso || 0}%`;
  return `NIST ${result.nist || 0}% / ISO ${result.iso || 0}%`;
}

function scoreLevel(value) {
  if (value >= 85) return { label: "Solido", tone: "strong" };
  if (value >= 70) return { label: "Bueno", tone: "good" };
  if (value >= 50) return { label: "En mejora", tone: "warn" };
  return { label: "Critico", tone: "danger" };
}

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("dashboard");
  const [evaluations, setEvaluations] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [activeResult, setActiveResult] = useState(null);

  async function loadData() {
    const [questionsRes, evaluationsRes, companiesRes] = await Promise.all([
      fetch(`${API}/questions`),
      fetch(`${API}/evaluations`),
      fetch(`${API}/companies`),
    ]);
    setQuestions(await questionsRes.json());
    setEvaluations(await evaluationsRes.json());
    setCompanies(await companiesRes.json());
  }

  useEffect(() => {
    if (user) loadData();
  }, [user]);

  useEffect(() => {
    const canCreateEvaluation = ["Auditor", "Administrador", "Empresa"].includes(user?.role);
    const canManageCompanies = ["Auditor", "Administrador"].includes(user?.role);
    if ((!canCreateEvaluation && view === "new") || (!canManageCompanies && view === "companies")) {
      setView("dashboard");
    }
  }, [user, view]);

  if (!user) return <ProfessionalLogin onLogin={setUser} />;

  const latest = activeResult || evaluations[0];
  const canCreateEvaluation = ["Auditor", "Administrador", "Empresa"].includes(user.role);
  const canManageCompanies = ["Auditor", "Administrador"].includes(user.role);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <strong>Evaluador TSI</strong>
            <span>NIST CSF + ISO 27001</span>
          </div>
        </div>
        <button className={view === "dashboard" ? "nav active" : "nav"} onClick={() => setView("dashboard")}>
          <BarChart3 size={18} /> Dashboard
        </button>
        {canCreateEvaluation && (
          <button className={view === "new" ? "nav active" : "nav"} onClick={() => setView("new")}>
            <Plus size={18} /> Nueva evaluacion
          </button>
        )}
        {canManageCompanies && (
          <button className={view === "companies" ? "nav active" : "nav"} onClick={() => setView("companies")}>
            <ClipboardCheck size={18} /> Empresas
          </button>
        )}
        <button className={view === "report" ? "nav active" : "nav"} onClick={() => setView("report")}>
          <FileText size={18} /> Reporte
        </button>
        <button className="nav logout" onClick={() => setUser(null)}>
          <LogOut size={18} /> Salir
        </button>
      </aside>

      <main className={view === "dashboard" ? "content dashboard-content" : "content module-content"}>
        <header className="topbar">
          <div>
            <p className="eyebrow">Prototipo funcional</p>
            <h1>Evaluador automatico NIST CSF 2.0 e ISO 27001</h1>
          </div>
          <div className="user-pill">{user.name} · {user.role}</div>
        </header>

        {!canCreateEvaluation && <ReadOnlyNotice />}
        {view === "dashboard" && <Dashboard evaluations={evaluations} latest={latest} />}
        {view === "new" && (
          <NewEvaluation
            user={user}
            questions={questions}
            companies={companies}
            onCompaniesChanged={loadData}
            onCreated={(created) => {
              setActiveResult(created);
              loadData();
              setView("report");
            }}
          />
        )}
        {view === "companies" && canManageCompanies && <Companies user={user} companies={companies} onCreated={loadData} />}
        {view === "report" && <Report evaluation={latest} />}
      </main>
    </div>
  );
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Digite usuario y contraseña");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) onLogin(data.user);
      else setError(data.message || "No se pudo iniciar sesion");
    } catch {
      setError("No se pudo conectar con el servidor local");
    } finally {
    setLoading(false);
    }
  }

  function loadDemoUser(type) {
    if (type === "reviewer") {
      setUsername("profesor");
      setPassword("tesis2026");
      return;
    }
    if (type === "company") {
      setUsername("empresa");
      setPassword("empresa2026");
      return;
    }
    setUsername("admin");
    setPassword("admin123");
  }

  return (
    <main className="login-page">
      <section className="login-layout">
        <div className="login-copy">
          <div className="login-mark">
            <ShieldCheck size={36} />
          </div>
          <p className="eyebrow">Proyecto final TSI</p>
          <h1>Evaluador automático de alineación y cumplimiento</h1>
          <p>
            Prototipo académico basado en NIST CSF 2.0 e ISO/IEC 27001 para registrar evaluaciones,
            calcular resultados ponderados y generar reportes ejecutivos.
          </p>
          <div className="login-highlights">
            <span>35 criterios</span>
            <span>Cálculo ponderado</span>
            <span>Reporte PDF</span>
          </div>
        </div>

        <div className="login-panel">
          <div className="login-title">
            <LockKeyhole size={26} />
            <div>
              <h2>Acceso al sistema</h2>
              <p>Módulo de autenticación del prototipo.</p>
            </div>
          </div>
          <form onSubmit={submit}>
            <label>
              Usuario
              <div className="input-with-icon">
                <UserRound size={18} />
                <input
                  value={username}
                  autoComplete="username"
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="Digite su usuario"
                />
              </div>
            </label>
            <label>
              Contraseña
              <div className="input-with-icon">
                <LockKeyhole size={18} />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  autoComplete="current-password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Digite su contraseña"
                />
                <button
                  className="ghost-icon"
                  type="button"
                  title={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>
            {error && <div className="error">{error}</div>}
            <button className="primary" disabled={loading}>{loading ? "Validando..." : "Iniciar sesión"}</button>
          </form>
          <div className="demo-access">
            <strong>Acceso de demostración local</strong>
            <div className="demo-actions">
              <button type="button" onClick={() => loadDemoUser("auditor")}>Cargar auditor</button>
              <button type="button" onClick={() => loadDemoUser("reviewer")}>Cargar revisor</button>
              <button type="button" onClick={() => loadDemoUser("company")}>Cargar empresa</button>
            </div>
            <span>Usuarios de prueba creados automáticamente en SQLite.</span>
          </div>
        </div>
      </section>
    </main>
  );
}

function ProfessionalLogin({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Digite usuario y contrasena");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) onLogin(data.user);
      else setError(data.message || "No se pudo iniciar sesion");
    } catch {
      setError("No se pudo conectar con el servidor local");
    } finally {
      setLoading(false);
    }
  }

  function loadDemoUser(type) {
    if (type === "reviewer") {
      setUsername("profesor");
      setPassword("tesis2026");
      return;
    }
    if (type === "company") {
      setUsername("empresa");
      setPassword("empresa2026");
      return;
    }
    setUsername("admin");
    setPassword("admin123");
  }

  return (
    <main className="login-page professional">
      <div className="login-shell-header">
        <div className="login-brandline">
          <ShieldCheck size={22} />
          <span>Cyber Compliance Lab</span>
        </div>
        <span className="environment-pill">MVP academico</span>
      </div>

      <section className="professional-login-layout">
        <div className="professional-login-copy">
          <div className="login-kicker">
            <ShieldCheck size={18} />
            <span>Proyecto final de Seguridad Informatica</span>
          </div>
          <h1>Evaluador automatico NIST CSF 2.0 e ISO/IEC 27001</h1>
          <p className="login-summary">
            Prototipo para registrar empresas, levantar evidencias, calcular brechas y generar reportes de cumplimiento.
          </p>

          <div className="assessment-preview" aria-hidden="true">
            <div className="preview-header">
              <span>Vista previa de auditoria</span>
              <strong>Activo</strong>
            </div>
            <div className="security-signal">
              <span>Politicas</span>
              <span>Inventario</span>
              <span>Accesos</span>
              <span>Incidentes</span>
              <span>Backups</span>
              <span>Reportes</span>
            </div>
            <div className="preview-row">
              <span>Alineacion NIST</span>
              <div className="preview-track"><i style={{ width: "82%" }} /></div>
              <b>82%</b>
            </div>
            <div className="preview-row">
              <span>Cumplimiento ISO</span>
              <div className="preview-track"><i style={{ width: "75%" }} /></div>
              <b>75%</b>
            </div>
            <div className="preview-row">
              <span>Brechas criticas</span>
              <div className="preview-track warning"><i style={{ width: "38%" }} /></div>
              <b>12</b>
            </div>
            <div className="audit-log">
              <code>&gt; evidencia recibida: Politica.pdf</code>
              <code>&gt; control PR-02: cumple parcialmente</code>
              <code>&gt; reporte ejecutivo listo</code>
            </div>
            <div className="preview-footer">
              <span>35 criterios</span>
              <span>Reporte PDF</span>
            </div>
          </div>
        </div>

        <div className="professional-login-panel">
          <div className="login-title">
            <div className="login-title-icon">
              <LockKeyhole size={22} />
            </div>
            <div>
              <h2>Acceso seguro</h2>
              <p>Selecciona un perfil o ingresa tus credenciales.</p>
            </div>
          </div>

          <form onSubmit={submit}>
            <label>
              Usuario
              <div className="input-with-icon">
                <UserRound size={18} />
                <input
                  value={username}
                  autoComplete="username"
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="Digite su usuario"
                />
              </div>
            </label>

            <label>
              Contrasena
              <div className="input-with-icon">
                <LockKeyhole size={18} />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  autoComplete="current-password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Digite su contrasena"
                />
                <button
                  className="ghost-icon"
                  type="button"
                  title={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>

            {error && <div className="error">{error}</div>}
            <button className="primary login-submit" disabled={loading}>
              {loading ? "Validando..." : "Iniciar sesion"}
            </button>
          </form>

          <div className="demo-access professional-demo">
            <strong>Perfiles de prueba</strong>
            <div className="demo-actions">
              <button type="button" onClick={() => loadDemoUser("auditor")}>
                <span>Auditor</span>
                <small>Crear y evaluar</small>
              </button>
              <button type="button" onClick={() => loadDemoUser("reviewer")}>
                <span>Revisor</span>
                <small>Consultar reportes</small>
              </button>
              <button type="button" onClick={() => loadDemoUser("company")}>
                <span>Empresa</span>
                <small>Responder evaluacion</small>
              </button>
            </div>
            <span>Estos perfiles existen solo para la demostracion academica.</span>
          </div>
        </div>
      </section>

      <div className="login-shell-footer">
        Instituto Tecnologico de Las Americas - Seguridad Informatica - Proyecto final TSI
      </div>
    </main>
  );
}

function Dashboard({ evaluations, latest }) {
  const companyOptions = Array.from(new Set(evaluations.map((item) => item.company))).sort();
  const [selectedCompany, setSelectedCompany] = useState("all");
  const [showAllRecent, setShowAllRecent] = useState(false);
  const filteredEvaluations = selectedCompany === "all"
    ? evaluations
    : evaluations.filter((item) => item.company === selectedCompany);
  const selectedLatest = filteredEvaluations[0] || latest;
  const results = selectedLatest?.results;
  const nistData = Object.entries(results?.nist_functions || results?.functions || {})
    .filter(([, value]) => value > 0)
    .map(([name, value], index) => ({ name, value, fill: chartPalette[index % chartPalette.length] }));
  const isoData = Object.entries(results?.iso_areas || {})
    .filter(([, value]) => value > 0)
    .map(([name, value], index) => ({ name, value, fill: chartPalette[(index + 1) % chartPalette.length] }));
  const responseData = Object.entries(results?.response_distribution || {})
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({ name: answerLabels[key], value, fill: responsePalette[key] }));
  const opportunities = results?.opportunities || results?.gaps?.slice(0, 5) || [];
  const selectedCompanyName = selectedCompany === "all" ? "Todas las empresas" : selectedCompany;
  const nistLevel = scoreLevel(results?.nist || 0);
  const isoLevel = scoreLevel(results?.iso || 0);
  const latestDate = selectedLatest?.date || "Sin evaluaciones";
  const latestFramework = selectedLatest ? frameworkLabel(selectedLatest.frameworks) : "Sin referente";
  const recentEvaluations = showAllRecent ? filteredEvaluations : filteredEvaluations.slice(0, 5);

  return (
    <div className="dashboard-suite">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <div className="filter-heading">
            <div className="filter-icon"><Building2 size={20} /></div>
            <div>
              <p className="eyebrow">Panel ejecutivo</p>
              <h2>{selectedCompanyName}</h2>
            </div>
          </div>
          <p>
            Ultima evaluacion: <strong>{latestDate}</strong> - Referente: <strong>{latestFramework}</strong>
          </p>
          <div className="dashboard-hero-meta">
            <span><ClipboardCheck size={16} /> {filteredEvaluations.length} evaluaciones</span>
            <span><AlertTriangle size={16} /> {results?.pending_controls || 0} brechas</span>
            <span><CheckCircle2 size={16} /> {results?.fulfilled_controls || 0} criterios cumplidos</span>
          </div>
        </div>

        <div className="dashboard-score-stack">
          <FrameworkScoreCard
            title="Alineacion NIST"
            value={results?.nist || 0}
            subtitle={nistLevel.label}
            tone={nistLevel.tone}
          />
          <FrameworkScoreCard
            title="Cumplimiento ISO"
            value={results?.iso || 0}
            subtitle={isoLevel.label}
            tone={isoLevel.tone}
          />
        </div>
      </section>

      <section className="dashboard-filter refined">
        <div className="filter-heading">
          <div className="filter-icon"><BarChart3 size={20} /></div>
          <div>
            <p className="eyebrow">Filtro</p>
            <h2>Analisis por empresa</h2>
          </div>
        </div>
        <div className="filter-control">
          <label>
            Empresa evaluada
            <select value={selectedCompany} onChange={(event) => setSelectedCompany(event.target.value)}>
              <option value="all">Todas las empresas</option>
              {companyOptions.map((company) => <option key={company} value={company}>{company}</option>)}
            </select>
          </label>
          <div className="filter-summary">
            <strong>{filteredEvaluations.length}</strong>
            <span>{filteredEvaluations.length === 1 ? "evaluacion" : "evaluaciones"}</span>
          </div>
        </div>
      </section>

      <section className="metrics executive-metrics">
        <Metric icon={<Activity />} label="Madurez" value={results ? `Nivel ${results.maturity}` : "Nivel 0"} tone="blue" />
        <Metric icon={<ClipboardCheck />} label="Aplicables" value={results?.applicable_controls || 0} tone="green" />
        <Metric icon={<CheckCircle2 />} label="Cumplidos" value={results?.fulfilled_controls || 0} tone="green" />
        <Metric icon={<AlertTriangle />} label="Brechas criticas" value={results?.critical_gaps || 0} tone="red" />
        <Metric icon={<FileText />} label="Sin evidencia" value={results?.criteria_without_evidence || 0} tone="amber" />
        <Metric icon={<BarChart3 />} label="Evaluaciones" value={filteredEvaluations.length} tone="blue" />
      </section>

      <section className="grid two">
        <div className="panel chart-panel">
          <div className="chart-title">
            <div>
              <p className="eyebrow">NIST CSF 2.0</p>
              <h2>Alineacion por funcion</h2>
            </div>
            <span>{nistData.length} funciones</span>
          </div>
          <div className="chart chart-bars">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={nistData} layout="vertical" margin={{ top: 8, right: 38, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(142, 216, 197, 0.18)" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} stroke="#a7c3c7" />
                <YAxis type="category" dataKey="name" width={82} stroke="#c7dcda" />
                <Tooltip formatter={(value) => [`${value}%`, "Resultado"]} cursor={{ fill: "rgba(27, 107, 122, 0.06)" }} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={22}>
                  {nistData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                  <LabelList dataKey="value" position="right" formatter={(value) => `${value}%`} fill="#eef8f6" fontWeight={800} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="function-score-grid">
            {nistData.map((item) => (
              <div className="function-score" key={item.name}>
                <i style={{ background: item.fill }} />
                <span>{item.name}</span>
                <strong>{item.value}%</strong>
              </div>
            ))}
            {!nistData.length && <p className="muted">No hay datos NIST en la evaluacion seleccionada.</p>}
          </div>
        </div>
        <div className="panel chart-panel">
          <div className="chart-title">
            <div>
              <p className="eyebrow">ISO/IEC 27001</p>
              <h2>Cumplimiento por area</h2>
            </div>
            <span>{isoData.length} areas</span>
          </div>
          <div className="chart chart-bars iso-bars">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={isoData} layout="vertical" margin={{ top: 8, right: 38, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(142, 216, 197, 0.18)" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} stroke="#a7c3c7" />
                <YAxis type="category" dataKey="name" width={138} stroke="#c7dcda" tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => [`${value}%`, "Resultado"]} cursor={{ fill: "rgba(47, 155, 124, 0.06)" }} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}>
                  {isoData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                  <LabelList dataKey="value" position="right" formatter={(value) => `${value}%`} fill="#eef8f6" fontWeight={800} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="risk-summary">
            <div><span>NIST</span><strong>{results?.nist || 0}%</strong></div>
            <div><span>ISO</span><strong>{results?.iso || 0}%</strong></div>
          </div>
        </div>
      </section>

      <section className="grid two">
        <div className="panel chart-panel">
          <div className="chart-title">
            <div>
              <p className="eyebrow">Trazabilidad</p>
              <h2>Distribucion de respuestas</h2>
            </div>
          </div>
          <div className="chart donut-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={responseData} dataKey="value" innerRadius={68} outerRadius={104} paddingAngle={4}>
                  {responseData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(value) => [`${value}`, "Criterios"]} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <strong>{results?.applicable_controls || 0}</strong>
              <span>aplicables</span>
            </div>
          </div>
          <div className="chart-legend response-legend">
            {responseData.map((item) => (
              <span key={item.name}><i style={{ background: item.fill }} /> {item.name}: {item.value}</span>
            ))}
          </div>
        </div>

        <div className="panel">
          <p className="eyebrow">Prioridad</p>
          <h2>Principales oportunidades de mejora</h2>
          <div className="opportunity-list">
            {opportunities.map((item, index) => (
              <div className="opportunity" key={`${item.id}-${index}`}>
                <span className={item.severity === "Critica" ? "badge danger" : "badge"}>{item.severity}</span>
                <strong>{item.id} - {item.group}</strong>
                <p>{item.recommendation}</p>
              </div>
            ))}
            {!opportunities.length && <p className="muted">No hay oportunidades de mejora registradas para esta evaluacion.</p>}
          </div>
        </div>
      </section>

      <section className="panel recent-panel">
        <div className="chart-title">
          <div>
            <p className="eyebrow">Historial</p>
            <h2>Evaluaciones recientes</h2>
          </div>
          <span>{showAllRecent ? "Historial completo" : `Ultimas ${recentEvaluations.length}`}</span>
        </div>
        <div className="recent-list">
          {recentEvaluations.map((item) => (
            <article className="recent-card" key={item.id}>
              <div className="recent-icon">
                <ClipboardCheck size={20} />
              </div>
              <div className="recent-main">
                <strong>{item.company}</strong>
                <span>{item.date} - {item.auditor}</span>
              </div>
              <span className="framework-chip">{frameworkLabel(item.frameworks)}</span>
              <div className="recent-score">
                <strong>{formatEvaluationResult(item)}</strong>
                <small>{item.results?.pending_controls || 0} brechas</small>
              </div>
            </article>
          ))}
          {!recentEvaluations.length && <p className="muted">No hay evaluaciones para este filtro.</p>}
        </div>
        {filteredEvaluations.length > 5 && (
          <div className="recent-footer">
            <p className="recent-note">
              {showAllRecent
                ? `Mostrando ${filteredEvaluations.length} evaluaciones registradas para este filtro.`
                : `Mostrando las 5 evaluaciones mas recientes de ${filteredEvaluations.length} registradas para este filtro.`}
            </p>
            <button className="secondary-action" type="button" onClick={() => setShowAllRecent(!showAllRecent)}>
              {showAllRecent ? "Mostrar menos" : "Ver todos los registros"}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function FrameworkScoreCard({ title, value, subtitle, tone }) {
  return (
    <div className={`framework-card ${tone}`}>
      <div className="framework-ring" style={{ "--score": `${value}%` }}>
        <strong>{value}%</strong>
      </div>
      <div>
        <span>{title}</span>
        <strong>{subtitle}</strong>
        <small>Resultado interno de la matriz</small>
      </div>
    </div>
  );
}

function Metric({ icon, label, value, tone = "blue" }) {
  return (
    <div className={`metric ${tone}`}>
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReadOnlyNotice() {
  return (
    <section className="permission-notice">
      <LockKeyhole size={18} />
      <span>Modo revisor: puedes consultar dashboard, resultados y reportes. El registro y respuesta de evaluaciones queda reservado a perfiles autorizados.</span>
    </section>
  );
}

function Companies({ user, companies, onCreated }) {
  const [form, setForm] = useState({ name: "", sector: "", employees: "", auditor_responsible: "", contact: "", notes: "" });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    const res = await fetch(`${API}/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-Role": user.role },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (res.ok) {
      setForm({ name: "", sector: "", employees: "", auditor_responsible: "", contact: "", notes: "" });
      setMessage("Empresa registrada correctamente.");
      onCreated();
    } else {
      setMessage(data.message || "No se pudo registrar la empresa.");
    }
    setSaving(false);
  }

  function update(field, value) {
    setForm({ ...form, [field]: value });
  }

  return (
    <>
      <section className="panel">
        <h2>Registrar empresa</h2>
        <form className="company-form" onSubmit={submit}>
          <label>Nombre<input value={form.name} onChange={(event) => update("name", event.target.value)} required /></label>
          <label>Sector<input value={form.sector} onChange={(event) => update("sector", event.target.value)} placeholder="Servicios, comercio, salud..." /></label>
          <label>Empleados<input type="number" min="1" value={form.employees} onChange={(event) => update("employees", event.target.value)} placeholder="35" /></label>
          <label>Auditor responsable<input value={form.auditor_responsible} onChange={(event) => update("auditor_responsible", event.target.value)} placeholder="Maria Perez" /></label>
          <label>Contacto<input value={form.contact} onChange={(event) => update("contact", event.target.value)} placeholder="correo o telefono" /></label>
          <label className="wide">Notas<input value={form.notes} onChange={(event) => update("notes", event.target.value)} placeholder="Alcance o comentario general" /></label>
          <button className="primary" disabled={saving}>{saving ? "Guardando..." : "Guardar empresa"}</button>
        </form>
        {message && <p className="form-message">{message}</p>}
      </section>

      <section className="panel">
        <h2>Empresas registradas</h2>
        <div className="table company-table">
          <div className="row head"><span>Empresa</span><span>Sector</span><span>Empleados</span><span>Auditor</span></div>
          {companies.map((company) => (
            <div className="row" key={company.id}>
              <span>{company.name}</span>
              <span>{company.sector || "No especificado"}</span>
              <span>{company.employees || "No especificado"}</span>
              <span>{company.auditor_responsible || "No especificado"}</span>
            </div>
          ))}
          {!companies.length && <p className="muted">Todavia no hay empresas registradas.</p>}
        </div>
      </section>
    </>
  );
}

function NewEvaluation({ user, questions, companies, onCompaniesChanged, onCreated }) {
  const [company, setCompany] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [auditor, setAuditor] = useState("Jeissel");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [frameworks, setFrameworks] = useState("both");
  const [answers, setAnswers] = useState({});
  const [evidenceNotes, setEvidenceNotes] = useState({});
  const [evidenceFiles, setEvidenceFiles] = useState({});
  const [saving, setSaving] = useState(false);
  const [activeGroupKey, setActiveGroupKey] = useState("");
  const canRegisterCompany = ["Auditor", "Administrador"].includes(user.role);

  useEffect(() => {
    if (!company && companies?.length) setCompany(companies[0].name);
  }, [companies, company]);

  const selectedCompany = useMemo(() => {
    return companies.find((item) => item.name === company);
  }, [companies, company]);

  useEffect(() => {
    if (selectedCompany?.auditor_responsible && auditor === "Jeissel") {
      setAuditor(selectedCompany.auditor_responsible);
    }
  }, [selectedCompany, auditor]);

  const filteredQuestions = useMemo(() => {
    if (frameworks === "NIST") return questions.filter((question) => question.framework === "NIST");
    if (frameworks === "ISO") return questions.filter((question) => question.framework === "ISO");
    return questions;
  }, [questions, frameworks]);

  const answeredCount = filteredQuestions.filter((question) => answers[question.id]).length;
  const progress = filteredQuestions.length ? Math.round((answeredCount / filteredQuestions.length) * 100) : 0;

  const grouped = useMemo(() => {
    return filteredQuestions.reduce((acc, question) => {
      const key = `${frameworkLabel(question.framework)} - ${question.group}`;
      acc[key] = acc[key] || [];
      acc[key].push(question);
      return acc;
    }, {});
  }, [filteredQuestions]);

  const groupEntries = useMemo(() => Object.entries(grouped), [grouped]);

  useEffect(() => {
    if (!groupEntries.length) return;
    if (!groupEntries.some(([key]) => key === activeGroupKey)) {
      setActiveGroupKey(groupEntries[0][0]);
    }
  }, [activeGroupKey, groupEntries]);

  const activeIndex = Math.max(0, groupEntries.findIndex(([key]) => key === activeGroupKey));
  const activeEntry = groupEntries[activeIndex] || groupEntries[0];
  const activeGroupTitle = activeEntry?.[0] || "";
  const activeItems = activeEntry?.[1] || [];

  function countAnswered(items) {
    return items.filter((question) => answers[question.id]).length;
  }

  function groupKeyFor(question) {
    return `${frameworkLabel(question.framework)} - ${question.group}`;
  }

  async function ensureCompany() {
    const selected = newCompany.trim() || company;
    if (!newCompany.trim()) return selected;
    if (!canRegisterCompany) throw new Error("Este perfil no puede registrar empresas nuevas.");

    const res = await fetch(`${API}/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-Role": user.role },
      body: JSON.stringify({ name: selected }),
    });
    if (res.ok || res.status === 409) {
      onCompaniesChanged();
      return selected;
    }
    throw new Error("No se pudo registrar la empresa");
  }

  async function uploadEvidenceFiles() {
    const uploaded = {};
    const allowedQuestionIds = new Set(filteredQuestions.map((question) => question.id));
    for (const [questionId, files] of Object.entries(evidenceFiles)) {
      if (!allowedQuestionIds.has(questionId)) continue;
      uploaded[questionId] = [];
      for (const file of files) {
        const formData = new FormData();
        formData.append("question_id", questionId);
        formData.append("file", file);
        const res = await fetch(`${API}/evidence`, {
          method: "POST",
          headers: { "X-User-Role": user.role },
          body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "No se pudo subir una evidencia");
        uploaded[questionId].push(data);
      }
    }
    return uploaded;
  }

  async function submit(event) {
    event.preventDefault();
    const missingAnswer = filteredQuestions.find((question) => !answers[question.id]);
    if (missingAnswer) {
      setActiveGroupKey(groupKeyFor(missingAnswer));
      alert(`Falta responder el criterio ${missingAnswer.id}.`);
      return;
    }
    const missingJustification = filteredQuestions.find((question) => {
      return answers[question.id] === "na" && !(evidenceNotes[question.id] || "").trim();
    });
    if (missingJustification) {
      setActiveGroupKey(groupKeyFor(missingJustification));
      alert(`El criterio ${missingJustification.id} esta marcado como No aplica y requiere justificacion.`);
      return;
    }
    setSaving(true);
    try {
      const selectedCompany = await ensureCompany();
      const uploadedFiles = await uploadEvidenceFiles();
      const evidence = {};
      const filteredAnswers = {};
      filteredQuestions.forEach((question) => {
        if (answers[question.id]) filteredAnswers[question.id] = answers[question.id];
        const note = evidenceNotes[question.id] || "";
        const files = uploadedFiles[question.id] || [];
        if (note || files.length) evidence[question.id] = { note, files };
      });

      const res = await fetch(`${API}/evaluations`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-User-Role": user.role },
        body: JSON.stringify({ company: selectedCompany, auditor, date, frameworks, answers: filteredAnswers, evidence }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "No se pudo guardar la evaluacion");
      onCreated({ id: data.id, company: selectedCompany, auditor, date, frameworks, results: data.results, evidence });
    } catch (error) {
      alert(error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="evaluation-form" onSubmit={submit}>
      <section className="panel form-grid">
        <label>
          Empresa registrada
          <select value={company} onChange={(event) => setCompany(event.target.value)} required={!newCompany.trim()}>
            {companies.map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}
          </select>
        </label>
        <label>
          Nueva empresa
          {canRegisterCompany ? (
            <input value={newCompany} onChange={(event) => setNewCompany(event.target.value)} placeholder="Opcional: registrar al evaluar" />
          ) : (
            <input value="Reservado al auditor" disabled />
          )}
        </label>
        <label>Fecha<input type="date" value={date} onChange={(event) => setDate(event.target.value)} required /></label>
        <label>Auditor<input value={auditor} onChange={(event) => setAuditor(event.target.value)} required /></label>
        <label>
          Marco a evaluar
          <select value={frameworks} onChange={(event) => setFrameworks(event.target.value)}>
            <option value="both">NIST CSF 2.0 + ISO/IEC 27001</option>
            <option value="NIST">Solo NIST CSF 2.0</option>
            <option value="ISO">Solo ISO/IEC 27001</option>
          </select>
        </label>
      </section>

      <section className="assessment-progress">
        <div>
          <p className="eyebrow">Progreso del cuestionario</p>
          <strong>{answeredCount} de {filteredQuestions.length} criterios respondidos</strong>
        </div>
        <div className="progress-track"><i style={{ width: `${progress}%` }} /></div>
        <span>{progress}%</span>
      </section>

      <section className="question-workspace">
        <aside className="question-nav-panel">
          <p className="eyebrow">Matriz de criterios</p>
          <h2>Funciones y areas</h2>
          <div className="question-group-list">
            {groupEntries.map(([group, items], index) => {
              const answeredInGroup = countAnswered(items);
              const isActive = group === activeGroupKey;
              return (
                <button
                  className={isActive ? "question-group-tab active" : "question-group-tab"}
                  key={group}
                  type="button"
                  onClick={() => setActiveGroupKey(group)}
                >
                  <span>{index + 1}</span>
                  <strong>{group}</strong>
                  <small>{answeredInGroup}/{items.length} respondidos</small>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="panel questionnaire-panel">
          <div className="questionnaire-head">
            <div>
              <p className="eyebrow">Bloque activo</p>
              <h2>{activeGroupTitle}</h2>
              <p className="module-objective">{moduleObjectives[activeItems[0]?.group]}</p>
            </div>
            <div className="block-counter">
              <strong>{countAnswered(activeItems)}/{activeItems.length}</strong>
              <span>criterios</span>
            </div>
          </div>

          <div className="question-grid">
            {activeItems.map((question) => {
              const questionNumber = filteredQuestions.findIndex((item) => item.id === question.id) + 1;
              return (
                <div className="question question-card" key={question.id}>
                  <div className="question-card-head">
                    <span>{question.id}</span>
                    <small>Pregunta {questionNumber} de {filteredQuestions.length}</small>
                  </div>
                  <div>
                    <strong>{question.question}</strong>
                    <small>Criterio: {question.criterion}</small>
                    <small>Referente: {frameworkLabel(question.framework)} - Peso: {question.weight}</small>
                    <small>Evidencia esperada: {question.evidence_expected}</small>
                  </div>
                  <div className="answers compact-answers">
                    {Object.entries(answerLabels).map(([value, label]) => (
                      <label className={answers[question.id] === value ? "radio selected" : "radio"} key={value}>
                        <input
                          type="radio"
                          name={question.id}
                          value={value}
                          checked={answers[question.id] === value}
                          required
                          onChange={() => setAnswers({ ...answers, [question.id]: value })}
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                  <input
                    className="evidence"
                    value={evidenceNotes[question.id] || ""}
                    required={answers[question.id] === "na"}
                    placeholder={answers[question.id] === "na" ? "Justificacion obligatoria para No aplica" : "Justificacion u observacion"}
                    onChange={(event) => setEvidenceNotes({ ...evidenceNotes, [question.id]: event.target.value })}
                  />
                  <input
                    className="evidence-file"
                    type="file"
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.xlsx,.txt"
                    onChange={(event) => setEvidenceFiles({ ...evidenceFiles, [question.id]: Array.from(event.target.files) })}
                  />
                </div>
              );
            })}
          </div>

          <div className="questionnaire-actions">
            <button
              className="secondary-action"
              type="button"
              disabled={activeIndex <= 0}
              onClick={() => setActiveGroupKey(groupEntries[activeIndex - 1]?.[0])}
            >
              Anterior bloque
            </button>
            <button
              className="secondary-action"
              type="button"
              disabled={activeIndex >= groupEntries.length - 1}
              onClick={() => setActiveGroupKey(groupEntries[activeIndex + 1]?.[0])}
            >
              Siguiente bloque
            </button>
            <button className="primary" disabled={saving}>{saving ? "Calculando..." : "Finalizar evaluacion"}</button>
          </div>
        </section>
      </section>
    </form>
  );
}

function Report({ evaluation }) {
  if (!evaluation) {
    return <section className="panel"><h2>Reporte</h2><p className="muted">Todavia no hay evaluaciones generadas.</p></section>;
  }
  const result = evaluation.results;
  const evidenceEntries = Object.entries(evaluation.evidence || {}).filter(([, value]) => value);
  return (
    <section className="panel report">
      <div className="report-head">
        <div>
          <p className="eyebrow">Reporte ejecutivo</p>
          <h2>{evaluation.company}</h2>
          <p>{evaluation.date} - {evaluation.auditor} - {frameworkLabel(evaluation.frameworks)}</p>
        </div>
        <a className="primary link-button" href={`${API}/evaluations/${evaluation.id}/report`}>
          <Download size={18} /> Generar PDF
        </a>
      </div>
      <p className="report-disclaimer">
        Los resultados representan una evaluacion interna basada en criterios seleccionados del modelo y no constituyen una certificacion oficial.
      </p>
      <section className="metrics compact">
        <Metric icon={<ShieldCheck />} label="Alineacion NIST" value={`${result.nist}%`} />
        <Metric icon={<FileText />} label="Cumplimiento ISO" value={`${result.iso}%`} />
        <Metric icon={<ClipboardCheck />} label="Cumplidos" value={result.fulfilled_controls || 0} />
        <Metric icon={<FileText />} label="Pendientes" value={result.pending_controls || 0} />
        <Metric icon={<Gauge />} label="Sin evidencia" value={result.criteria_without_evidence || 0} />
        <Metric icon={<ClipboardCheck />} label="Madurez" value={`Nivel ${result.maturity}`} />
      </section>
      <h3>Brechas y recomendaciones</h3>
      {result.gaps.map((gap, index) => (
        <div className="gap" key={`${gap.question}-${index}`}>
          <span className={gap.severity === "Critica" ? "badge danger" : "badge"}>{gap.severity}</span>
          <strong>{gap.id ? `${gap.id}. ` : ""}{gap.question}</strong>
          <small>{gap.framework} - {gap.group} - {answerLabels[gap.answer] || "Respuesta evaluada"}</small>
          {gap.gap && <p>Brecha: {gap.gap}</p>}
          <p>{gap.recommendation}</p>
        </div>
      ))}
      {!result.gaps.length && <p className="muted">No se identificaron brechas relevantes.</p>}

      <h3>Evidencias registradas</h3>
      <div className="evidence-list">
        {evidenceEntries.map(([questionId, value]) => {
          const note = typeof value === "string" ? value : value.note;
          const files = typeof value === "object" ? value.files || [] : [];
          return (
            <div className="evidence-item" key={questionId}>
              <strong>{questionId}</strong>
              {note && <span>{note}</span>}
              {files.map((file) => (
                <a key={file.stored_name} href={`${API.replace("/api", "")}${file.url}`}>
                  {file.file_name}
                </a>
              ))}
            </div>
          );
        })}
        {!evidenceEntries.length && <p className="muted">No se registraron evidencias para esta evaluacion.</p>}
      </div>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
