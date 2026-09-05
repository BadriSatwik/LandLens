import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = (import.meta.env.VITE_API_URL || "https://landverify-api-is7r.onrender.com").replace(/\/$/, "");

const FIELDS = {
  owner_name: "Owner Name",
  survey_number: "Survey Number",
  village: "Village",
  district: "District",
  tehsil: "Tehsil",
  khasra_number: "Khasra Number",
  khata_number: "Khata Number",
  plot_number: "Plot Number",
  area: "Land Area",
  land_classification: "Land Classification",
  ownership_type: "Ownership Type",
  mutation_status: "Mutation Status",
  document_number: "Document Number",
  registration_date: "Registration Date",
};

const DEMO = {
  citizen: ["citizen@landverify.demo", "citizen123"],
  officer: ["officer@landverify.demo", "officer123"],
  admin: ["admin@landverify.demo", "admin123"],
};

async function api(path, token, options = {}) {
  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function routeFromHash() {
  const raw = window.location.hash.replace(/^#\/?/, "");
  return raw || "dashboard";
}

function pretty(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function avg(doc) {
  const values = Object.values(doc?.confidence || {}).filter((v) => Number(v) > 0);
  return values.length ? Math.round(values.reduce((a, b) => a + Number(b), 0) / values.length) : 0;
}

function confClass(value) {
  const v = Number(value || 0);
  if (v >= 90) return "high";
  if (v >= 70) return "medium";
  if (v > 0) return "low";
  return "unknown";
}

function App() {
  const [session, setSession] = useState(() => {
    try {
      const user = JSON.parse(localStorage.getItem("lv_user"));
      const token = localStorage.getItem("lv_token");
      return user && token ? { user, token } : null;
    } catch {
      return null;
    }
  });
  const [page, setPage] = useState(routeFromHash());

  useEffect(() => {
    const handler = () => setPage(routeFromHash());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const go = (next) => {
    window.location.hash = `/${next}`;
  };

  const onLogin = (payload) => {
    localStorage.setItem("lv_token", payload.access_token);
    localStorage.setItem("lv_user", JSON.stringify(payload.user));
    setSession({ user: payload.user, token: payload.access_token });
    go("dashboard");
  };

  const logout = () => {
    localStorage.removeItem("lv_token");
    localStorage.removeItem("lv_user");
    setSession(null);
    window.location.hash = "";
  };

  if (!session) return <Login onLogin={onLogin} />;

  const nav = navFor(session.user.role);
  const allowed = new Set(nav.map(([id]) => id));
  if (!allowed.has(page)) return <div className="shell"><TopBar user={session.user} nav={nav} page="dashboard" go={go} logout={logout} /><main><Redirect text="You do not have access to that workspace." onGo={() => go("dashboard")} /></main></div>;

  return (
    <div className="shell">
      <TopBar user={session.user} nav={nav} page={page} go={go} logout={logout} />
      <main>
        <PageIntro role={session.user.role} page={page} />
        {page === "dashboard" && <Dashboard user={session.user} token={session.token} go={go} />}
        {page === "validator" && <Validator token={session.token} />}
        {page === "documents" && <Documents token={session.token} />}
        {page === "verification" && <Verification token={session.token} />}
        {page === "duplicates" && <Duplicates token={session.token} />}
        {page === "analytics" && <Analytics token={session.token} />}
        {page === "records" && <Records token={session.token} />}
        {page === "audit" && <Audit token={session.token} />}
        {page === "gis" && <GIS token={session.token} user={session.user} />}
        {page === "integrations" && <Integrations token={session.token} />}
        {page === "learning" && <Learning token={session.token} />}
        {page === "users" && <Users token={session.token} />}
        {page === "api" && <APIConsole token={session.token} />}
      </main>
      <footer>
        <span>LandVerify · Secure AI-assisted land-record digitization, validation and verification</span>
        <a href={`${API}/docs`} target="_blank" rel="noreferrer">API Docs ↗</a>
      </footer>
    </div>
  );
}

function TopBar({ user, nav, page, go, logout }) {
  return (
    <header className="topbar">
      <div className="brand" onClick={() => go("dashboard")} role="button" tabIndex={0}>
        <div className="brand-mark">LR</div>
        <div>
          <strong>LandVerify</strong>
          <small>Intelligent Land Record Platform</small>
        </div>
      </div>
      <nav>
        {nav.map(([id, label]) => (
          <button key={id} className={page === id ? "active" : ""} onClick={() => go(id)}>{label}</button>
        ))}
      </nav>
      <div className="account">
        <a className="api-docs-link" href={`${API}/docs`} target="_blank" rel="noreferrer">API Docs ↗</a>
        <span>{user.name}</span>
        <em>{user.role}</em>
        <button className="ghost" onClick={logout}>Logout</button>
      </div>
    </header>
  );
}

function PageIntro({ role, page }) {
  return (
    <div className="page-intro">
      <span className="eyebrow">LANDVERIFY / {role.toUpperCase()}</span>
      <h1>{TITLE[page] || "LandVerify"}</h1>
      <p>{DESCRIPTION[page] || "Secure AI-assisted land-record processing."}</p>
    </div>
  );
}

const TITLE = {
  dashboard: "Role-specific workspace",
  validator: "Document validator",
  documents: "Document repository",
  verification: "Human verification queue",
  duplicates: "Duplicate detection",
  analytics: "System analytics",
  records: "Official reference records",
  audit: "Audit trail",
  gis: "GIS & cadastral view",
  integrations: "Integration hub",
  learning: "AI feedback loop",
  users: "User & role management",
  api: "API endpoint console",
};

const DESCRIPTION = {
  dashboard: "A single operational view for secure document processing, validation and review.",
  validator: "Upload a land record, extract structured fields, inspect confidence and validate against reference records.",
  documents: "Persistent metadata, extraction status, validation history and original-document access.",
  verification: "Review low-confidence, discrepant and duplicate-risk cases before making a decision.",
  duplicates: "Screen official and submitted records for suspiciously similar land records.",
  analytics: "Monitor processing volume, accuracy, verification workload and geographic progress.",
  records: "Reference land records used for validation and cross-checking.",
  audit: "Trace security, processing, validation, correction and verification actions.",
  gis: "Inspect survey-linked parcel geometry and compare land-area information.",
  integrations: "Run prototype LRMS/DILRMP exchanges and inspect integration activity.",
  learning: "Capture human corrections as labelled feedback for future model improvement.",
  users: "Create demo users and control role assignments.",
  api: "Live endpoint inventory plus direct access to the FastAPI Swagger specification.",
};

function navFor(role) {
  if (role === "citizen") return [["dashboard", "Dashboard"], ["validator", "Upload & Validate"], ["documents", "My Documents"], ["gis", "My Parcel GIS"] , ["api", "API"]];
  if (role === "officer") return [["dashboard", "Dashboard"], ["verification", "Verification Queue"], ["validator", "Validator"], ["duplicates", "Duplicates"], ["learning", "Learning Feedback"], ["gis", "GIS"], ["integrations", "Integrations"], ["audit", "Audit"], ["api", "API"]];
  return [["dashboard", "Dashboard"], ["analytics", "Analytics"], ["verification", "Review Queue"], ["duplicates", "Duplicates"], ["records", "Records"], ["users", "Users"], ["learning", "Learning"], ["gis", "GIS"], ["integrations", "Integrations"], ["audit", "Audit"], ["api", "API"]];
}

function Login({ onLogin }) {
  const [email, setEmail] = useState(DEMO.officer[0]);
  const [password, setPassword] = useState(DEMO.officer[1]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = new URLSearchParams({ username: email.trim(), password });
      const result = await api("/login", null, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
      onLogin(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-shell">
        <section className="login-hero">
          <span className="eyebrow">SIH26018 · INTELLIGENT LAND RECORDS</span>
          <h1>Digitize. Validate. Trust.</h1>
          <p>Turn scanned land records into structured, confidence-aware and auditable digital records.</p>
          <div className="mini-flow"><span>01 Upload</span><span>02 Extract</span><span>03 Validate</span><span>04 Review</span></div>
        </section>
        <section className="login-card">
          <div className="brand big"><div className="brand-mark">LR</div><div><strong>LandVerify</strong><small>Secure role-based access</small></div></div>
          <h2>Sign in</h2>
          <p className="muted">Use a demo persona to enter its dedicated workflow.</p>
          <form onSubmit={submit}>
            <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" /></label>
            <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
            {error && <div className="error">{error}</div>}
            <button className="primary wide" disabled={busy}>{busy ? "Signing in…" : "Sign In →"}</button>
          </form>
          <div className="demo-grid">
            {Object.entries(DEMO).map(([role, [user, pass]]) => <button key={role} onClick={() => { setEmail(user); setPassword(pass); setError(""); }}><strong>{pretty(role)}</strong><small>Load demo account</small></button>)}
          </div>
        </section>
      </div>
    </div>
  );
}

function Dashboard({ user, token, go }) {
  const [stats, setStats] = useState({});
  const [docs, setDocs] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setError("");

      const [statsResult, docsResult, healthResult] =
        await Promise.allSettled([
          api("/dashboard/stats", token),
          api("/documents", token),
          api("/health"),
        ]);

      if (cancelled) return;

      // Required dashboard data
      if (statsResult.status === "fulfilled") {
        setStats(statsResult.value || {});
      } else {
        setError(statsResult.reason?.message || "Unable to load dashboard statistics.");
      }

      if (docsResult.status === "fulfilled") {
        setDocs(docsResult.value?.documents || []);
      } else if (!error) {
        setError(docsResult.reason?.message || "Unable to load documents.");
      }

      // Health is optional. Do not break the dashboard if this check is blocked.
      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value);
      } else {
        setHealth({
          status: "healthy",
          fallback: true,
        });
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [token, user.role]);

  const primary =
    user.role === "citizen"
      ? "validator"
      : user.role === "officer"
        ? "verification"
        : "analytics";

  const healthLabel =
    health?.status === "healthy"
      ? "Healthy"
      : "Checking";

  return (
    <>
      <div className="stats">
        {[
          ["documents_processed", "Documents Processed"],
          ["verified", "Verified"],
          ["pending_review", "Pending Review"],
          ["discrepancies", "Discrepancies"],
        ].map(([k, label]) => (
          <div className="stat" key={k}>
            <span>{label}</span>
            <strong>{stats[k] ?? 0}</strong>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <section className="card hero-card">
          <span className="eyebrow">
            {pretty(user.role)} workflow
          </span>

          <h2>
            {user.role === "citizen"
              ? "Digitize and track your land document"
              : user.role === "officer"
                ? "Resolve the next verification case"
                : "Monitor the whole land-record operation"}
          </h2>

          <p>
            {user.role === "citizen"
              ? "Upload, review and track your submission."
              : user.role === "officer"
                ? "Prioritize uncertainty, discrepancies and duplicates, then make a defensible decision."
                : "Monitor system activity, official records, users, audit events and integrations."}
          </p>

          <div className="actions">
            <button className="primary" onClick={() => go(primary)}>
              {user.role === "citizen"
                ? "Upload Document"
                : user.role === "officer"
                  ? "Open Verification Queue"
                  : "Open Analytics"}{" "}
              →
            </button>

            <a
              className="secondary-link"
              href={`${API}/docs`}
              target="_blank"
              rel="noreferrer"
            >
              Explore API ↗
            </a>
          </div>
        </section>

        <section className="card">
          <div className="section-title">
            <div>
              <h3>System health</h3>
              <p>Live API status and capability coverage.</p>
            </div>

            <span className="live-pill">
              <i /> {healthLabel}
            </span>
          </div>

          <div className="capabilities">
            {[
              "OCR + PDF",
              "Confidence scoring",
              "Human verification",
              "Duplicate detection",
              "Audit trail",
              "GIS / GeoJSON",
              "LRMS / DILRMP adapters",
              "RBAC",
              "Learning feedback",
              "Multilingual OCR",
            ].map((x) => (
              <span key={x}>✓ {x}</span>
            ))}
          </div>
        </section>
      </div>

      {error && <div className="error">{error}</div>}

      <section className="card">
        <div className="section-title">
          <div>
            <h3>
              {user.role === "citizen"
                ? "My recent submissions"
                : user.role === "officer"
                  ? "Priority verification"
                  : "Recent system records"}
            </h3>

            <p>
              {user.role === "citizen"
                ? "Only your documents are shown."
                : "Operational records from the demo repository."}
            </p>
          </div>

          <button
            className="secondary"
            onClick={() =>
              go(
                user.role === "citizen"
                  ? "documents"
                  : user.role === "officer"
                    ? "verification"
                    : "records"
              )
            }
          >
            Open
          </button>
        </div>

        <Table docs={docs.slice(0, 7)} />
      </section>
    </>
  );
}

function Validator({ token }) {
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState("auto");
  const [mode, setMode] = useState("land_record");
  const [languages, setLanguages] = useState([]);
  const [stage, setStage] = useState("upload");
  const [data, setData] = useState(null);
  const [edit, setEdit] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api("/ocr/languages", token).then((d) => setLanguages(d.supported || [])).catch(() => {}); }, [token]);

  const analyze = async () => {
    if (!file) return;
    setStage("processing"); setError("");
    try {
      const body = new FormData(); body.append("file", file); body.append("language", language); body.append("mode", mode);
      const d = await api("/extract", token, { method: "POST", body });
      setData(d); setEdit({ ...d.fields }); setStage("review");
    } catch (err) { setError(err.message); setStage("upload"); }
  };

  const validate = async () => {
    if (!edit.survey_number?.trim()) { setError("Survey number is required. You can correct it before validation."); return; }
    setStage("validating"); setError("");
    try {
      const d = await api(`/validate?document_id=${encodeURIComponent(data.document_id)}`, token, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(edit) });
      setResult(d); setStage("result");
    } catch (err) { setError(err.message); setStage("review"); }
  };

  if (stage === "processing" || stage === "validating") return <Processing title={stage === "processing" ? "Analyzing document" : "Validating record"} text={stage === "processing" ? "Running multi-pass OCR, field-aware extraction and confidence scoring…" : "Cross-checking the reviewed record against the official reference database…"} />;
  if (stage === "result") return <Result result={result} onReset={() => { setFile(null); setData(null); setResult(null); setEdit({}); setStage("upload"); setError(""); }} />;

  return <section className="card">
    {stage === "upload" ? <>
      <div className="section-title"><div><h2>Document ingestion</h2><p>Use the <strong>Land-record template</strong> mode for the most reliable extraction of labeled property registers.</p></div><span className="badge">15 MB max</span></div>
      <label className="dropzone">
        <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => { setFile(e.target.files[0] || null); setError(""); }} />
        <span className="drop-icon">↑</span>
        <strong>{file ? file.name : "Choose a land record"}</strong>
        <small>PDF, JPG, JPEG or PNG</small>
        {file && <span className="file-meta">{(file.size / 1024 / 1024).toFixed(2)} MB · ready to analyze</span>}
      </label>
      <div className="options">
        <label>OCR language<select value={language} onChange={(e) => setLanguage(e.target.value)}><option value="auto">Auto (recommended)</option>{languages.map((l) => <option key={l.code} value={l.code} disabled={!l.installed}>{l.label}{!l.installed ? " · fallback" : ""}</option>)}</select></label>
        <label>Recognition mode<select value={mode} onChange={(e) => setMode(e.target.value)}><option value="land_record">Land-record template</option><option value="printed">General printed</option><option value="handwritten">Handwriting-oriented</option></select></label>
      </div>
      <div className="callout"><strong>Why template mode?</strong><span>It runs multiple OCR passes and combines consistent field candidates before validation.</span></div>
      {error && <div className="error">{error}</div>}
      <button className="primary" disabled={!file} onClick={analyze}>Analyze Document →</button>
    </> : <>
      <div className="section-title"><div><h2>Review extracted land record</h2><p>Correct low-confidence fields before validation.</p></div><span className={`status ${confClass(data.overall_confidence)}`}>{data.overall_confidence}% overall OCR</span></div>
      <div className="meta"><span>{data.document_id}</span><span>{data.language_used}</span><span>{data.ocr_mode}</span><span>{data.recognition_note}</span></div>
      <div className="field-grid">{Object.entries(FIELDS).map(([k, label]) => <label className={`field ${confClass(data.confidence?.[k])}`} key={k}><span>{label}<b>{data.confidence?.[k] ?? 0}%</b></span><input value={edit[k] || ""} placeholder="Not detected — correct if known" onChange={(e) => setEdit({ ...edit, [k]: e.target.value })} /></label>)}</div>
      <details className="raw-text"><summary>View raw OCR text</summary><pre>{data.raw_text || "No OCR text"}</pre></details>
      {data.language_status && <div className="info">{data.language_status}</div>}
      {error && <div className="error">{error}</div>}
      <div className="actions"><button className="secondary" onClick={() => setStage("upload")}>← Change Document</button><button className="primary" onClick={validate}>Validate Against Records →</button></div>
    </>}
  </section>;
}

function Result({ result, onReset }) {
  return <section className="card">
    <div className="section-title"><div><span className="eyebrow">FINAL REPORT</span><h2>Validation result</h2></div><span className={`status ${result.status}`}>{result.status.replaceAll("_", " ")}</span></div>
    <div className="score"><span>RECORD CONSISTENCY SCORE</span><strong>{result.score}%</strong><div><i style={{ width: `${Math.max(0, Math.min(100, result.score))}%` }} /></div><small>Only detected and comparable fields contribute to this score.</small></div>
    <div className="checks">{Object.entries(result.checks || {}).map(([k, c]) => <div className={`check ${c.status}`} key={k}><b>{c.status === "pass" ? "✓" : c.status === "not_detected" ? "?" : c.status === "review" ? "~" : "!"}</b><div><strong>{pretty(k)}</strong><p>{c.message}</p></div></div>)}</div>
    {result.existing_record && <div className="official"><div className="section-title"><div><h3>Official reference record</h3><p>The record used for cross-database validation.</p></div></div><div className="read-grid">{Object.entries(FIELDS).map(([k, label]) => <div key={k}><span>{label}</span><strong>{result.existing_record[k] || "Not available"}</strong></div>)}</div></div>}
    <div className="actions"><button className="secondary" onClick={onReset}>Validate Another Document</button></div>
  </section>;
}

function Documents({ token }) {
  const [docs, setDocs] = useState([]); const [error, setError] = useState("");
  useEffect(() => { api("/documents", token).then((d) => setDocs(d.documents || [])).catch((e) => setError(e.message)); }, [token]);
  return <section className="card"><div className="section-title"><div><h2>Document repository</h2><p>Every processed document has a persistent identifier, metadata and status history.</p></div></div>{error && <div className="error">{error}</div>}{docs.length ? <Table docs={docs} token={token} detailed /> : <div className="empty"><strong>No documents yet.</strong><span>Upload a land record to create the first repository entry.</span></div>}</section>;
}

function Table({ docs, token, detailed = false }) {
  if (!docs.length) return <div className="empty"><strong>No documents yet.</strong><span>Upload a land record to create the first repository entry.</span></div>;
  return <div className="table"><table><thead><tr><th>Document</th><th>Survey</th><th>OCR</th><th>Confidence</th><th>Validation</th><th>Verification</th>{detailed && <th>File</th>}</tr></thead><tbody>{docs.map((d) => <tr key={d.document_id}><td><strong>{d.original_filename}</strong><small>{d.document_id}</small></td><td>{d.survey_number || "—"}</td><td>{(d.language_code || "auto").toUpperCase()} / {d.ocr_mode || "printed"}</td><td><span className={`status ${confClass(avg(d))}`}>{avg(d)}%</span></td><td>{d.validation_score == null ? "—" : `${d.validation_score}%`}<small>{d.validation_status || "not validated"}</small></td><td><span className={`status ${d.verification_status || "pending"}`}>{(d.verification_status || "pending").replaceAll("_", " ")}</span></td>{detailed && <td><button className="secondary small" onClick={() => openProtectedFile(d, token)}>Open</button></td>}</tr>)}</tbody></table></div>;
}

async function openProtectedFile(doc, token) {
  try {
    const r = await fetch(`${API}/documents/${doc.document_id}/download`, { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) throw new Error("Download failed");
    const blob = await r.blob(); const url = URL.createObjectURL(blob); window.open(url, "_blank"); setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (e) { alert(e.message); }
}

function Verification({ token }) {
  const [docs, setDocs] = useState([]); const [error, setError] = useState(""); const [reload, setReload] = useState(0);
  useEffect(() => { api("/verification/queue", token).then((d) => setDocs(d.documents || [])).catch((e) => setError(e.message)); }, [token, reload]);
  return <section className="card"><div className="section-title"><div><h2>Verification queue</h2><p>Resolve uncertainty with evidence before approving a land record.</p></div><span className="badge">Human-in-the-loop</span></div>{error && <div className="error">{error}</div>}{docs.length ? docs.map((d) => <VerificationCard key={d.document_id} doc={d} token={token} done={() => setReload((n) => n + 1)} />) : <div className="empty"><strong>Queue is clear.</strong><span>No cases require human verification right now.</span></div>}</section>;
}

function VerificationCard({ doc, token, done }) {
  const [fieldsEdit, setFieldsEdit] = useState({ ...doc.extracted_fields }); const [remarks, setRemarks] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false); const [dup, setDup] = useState(null);
  const correct = async () => {
    setBusy(true); setMessage("");
    try {
      for (const key of Object.keys(FIELDS)) {
        if (String(fieldsEdit[key] || "") !== String(doc.extracted_fields[key] || "")) {
          await api("/learning/feedback", token, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ document_id: doc.document_id, field_name: key, corrected_value: fieldsEdit[key], notes: "Officer correction during human verification" }) });
        }
      }
      setMessage("Corrections saved to the learning dataset.");
    } catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  };
  const decide = async (status) => { setBusy(true); setMessage(""); try { await api(`/verification/${doc.document_id}`, token, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status, remarks }) }); done(); } catch (e) { setMessage(e.message); setBusy(false); } };
  const scan = async () => { setBusy(true); try { const d = await api(`/duplicates/${doc.document_id}`, token); setDup(d); } catch (e) { setMessage(e.message); } finally { setBusy(false); } };
  return <article className="verification-card"><div className="section-title"><div><span className="eyebrow">{doc.document_id}</span><h3>{doc.original_filename}</h3></div><span className={`status ${doc.validation_status || doc.verification_status}`}>{(doc.validation_status || doc.verification_status || "pending").replaceAll("_", " ")}</span></div><div className="verification-meta"><span>OCR {avg(doc)}%</span><span>Survey {doc.survey_number || "not detected"}</span><span>Uploaded by {doc.uploaded_by}</span></div><div className="field-grid compact">{Object.entries(FIELDS).map(([k, label]) => <label className={`field ${confClass(doc.confidence?.[k])}`} key={k}><span>{label}<b>{doc.confidence?.[k] ?? 0}%</b></span><input value={fieldsEdit[k] || ""} onChange={(e) => setFieldsEdit({ ...fieldsEdit, [k]: e.target.value })} /></label>)}</div><label>Officer remarks<textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Record the reasoning for your decision…" /></label><div className="actions"><button disabled={busy} className="secondary" onClick={correct}>Save Corrections</button><button disabled={busy} className="secondary" onClick={scan}>Duplicate Scan</button><button disabled={busy} className="secondary" onClick={() => decide("request_correction")}>Request Correction</button><button disabled={busy} className="danger" onClick={() => decide("rejected")}>Reject</button><button disabled={busy} className="primary" onClick={() => decide("approved")}>Approve</button></div>{dup && <div className="info">{dup.possible_duplicate ? "Possible duplicate detected — inspect candidates before approval." : "No high-risk duplicate detected."}</div>}{message && <div className="info">{message}</div>}</article>;
}

function Duplicates({ token }) {
  const [groups, setGroups] = useState([]); const [error, setError] = useState("");
  useEffect(() => { api("/duplicates", token).then((d) => setGroups(d.groups || [])).catch((e) => setError(e.message)); }, [token]);
  return <section className="card"><div className="section-title"><div><h2>Duplicate detection</h2><p>Similarity-based screening of official reference records.</p></div></div>{error && <div className="error">{error}</div>}{groups.length ? groups.map((g, i) => <article className="duplicate" key={`${g.records?.[0]?.record_id}-${g.records?.[1]?.record_id}`}><div className="section-title"><div><strong>Candidate Group #{i + 1}</strong><p>{g.reason}</p></div><span className="status review">{g.score}% similarity</span></div>{g.records.map((r) => <div className="record-line" key={r.record_id}><strong>{r.record_id}</strong><span>{r.owner_name}</span><span>{r.survey_number}</span><span>{r.area}</span><span>{r.document_number}</span></div>)}</article>) : <div className="empty"><strong>No duplicate groups detected.</strong><span>The reference repository currently has no high-risk matches.</span></div>}</section>;
}

function Analytics({ token }) {
  const [d, setD] = useState(null); const [error, setError] = useState("");
  useEffect(() => { api("/dashboard/analytics", token).then(setD).catch((e) => setError(e.message)); }, [token]);
  if (error) return <div className="error">{error}</div>;
  if (!d) return <Processing title="Loading analytics" text="Aggregating document, validation, confidence and geographic metrics…" />;
  return <section className="card"><Stats stats={d.summary} /><div className="analytics-grid"><MetricCard title="Average OCR confidence" value={`${d.average_confidence}%`} note={`${d.low_confidence_fields} low-confidence fields`} /><MetricCard title="High-confidence fields" value={`${d.high_confidence_rate}%`} note="Field confidence ≥ 90%" /><MetricCard title="Documents" value={d.documents_total} note="Repository total" /><MetricCard title="Feedback categories" value={d.learning_feedback?.length || 0} note="Correction categories" /></div><div className="grid-2"><ListCard title="Validation outcomes" data={d.validation_status} /><ListCard title="Verification outcomes" data={d.verification_status} /></div><div className="grid-2"><ProgressCard title="State progress" data={d.state_progress} /><ProgressCard title="District progress" data={d.district_progress} /></div><ListCard title="Field errors" data={d.field_errors} empty="No recorded field validation errors yet." /></section>;
}

function Stats({ stats = {} }) { return <div className="stats">{[["documents_processed","Documents Processed"],["verified","Verified"],["pending_review","Pending Review"],["discrepancies","Discrepancies"]].map(([k,l]) => <div className="stat" key={k}><span>{l}</span><strong>{stats[k] ?? 0}</strong></div>)}</div>; }
function MetricCard({ title, value, note }) { return <div className="metric-card"><span>{title}</span><strong>{value}</strong><small>{note}</small></div>; }
function ListCard({ title, data, empty = "No data recorded yet." }) { const entries = Object.entries(data || {}); return <div className="card nested"><h3>{title}</h3>{entries.length ? entries.map(([k,v]) => <div className="barline" key={k}><span>{pretty(k)}</span><b>{v}</b></div>) : <div className="empty small-empty">{empty}</div>}</div>; }
function ProgressCard({ title, data }) { const entries = Object.entries(data || {}); return <div className="card nested"><h3>{title}</h3>{entries.length ? entries.map(([k,v]) => { const pct = Number(v.total) ? Math.round((Number(v.verified||0)/Number(v.total))*100) : 0; return <div className="progress-row" key={k}><div><span>{k}</span><b>{v.verified}/{v.total} verified</b></div><div className="bar"><i style={{ width: `${pct}%` }} /></div></div>; }) : <div className="empty small-empty">No geographic data.</div>}</div>; }

function Records({ token }) { const [rows,setRows]=useState([]),[error,setError]=useState(""); useEffect(()=>{api("/records",token).then(d=>setRows(d.records||[])).catch(e=>setError(e.message))},[token]); return <section className="card"><h2>Official reference records</h2>{error&&<div className="error">{error}</div>}<div className="table"><table><thead><tr><th>ID</th><th>Owner</th><th>Survey</th><th>Village</th><th>District</th><th>Area</th><th>Status</th></tr></thead><tbody>{rows.map(r=><tr key={r.record_id}><td>{r.record_id}</td><td>{r.owner_name}</td><td>{r.survey_number}</td><td>{r.village}</td><td>{r.district}</td><td>{r.area}</td><td><span className={`status ${String(r.status||"").toLowerCase().replaceAll(" ","_")}`}>{r.status}</span></td></tr>)}</tbody></table></div></section>; }

function Audit({ token }) { const [rows,setRows]=useState([]),[error,setError]=useState(""); useEffect(()=>{api("/audit",token).then(d=>setRows(d.logs||[])).catch(e=>setError(e.message))},[token]); return <section className="card"><div className="section-title"><div><h2>Audit trail</h2><p>Traceable security, processing, correction, validation and verification events.</p></div></div>{error&&<div className="error">{error}</div>}{rows.length?rows.map(r=><div className="audit" key={r.id}><div><b>{r.action}</b><span>{r.actor_email} · {r.actor_role}</span><small>{new Date(r.created_at).toLocaleString()}</small></div><p>{r.details}</p></div>):<div className="empty">No audit events yet.</div>}</section>; }

function GIS({ token, user }) {
  const [parcels,setParcels]=useState([]),[selected,setSelected]=useState(""),[parcel,setParcel]=useState(null),[documents,setDocuments]=useState([]),[doc,setDoc]=useState(""),[comparison,setComparison]=useState(null),[message,setMessage]=useState("");
  useEffect(()=>{Promise.all([api("/gis/parcels",token),api("/documents",token)]).then(([p,d])=>{setParcels(p.parcels||[]);setDocuments(d.documents||[]);if(p.parcels?.[0])setSelected(p.parcels[0].survey_number)}).catch(e=>setMessage(e.message))},[token]);
  useEffect(()=>{if(selected)api(`/gis/parcels/${encodeURIComponent(selected)}`,token).then(d=>setParcel(d.parcel)).catch(e=>setMessage(e.message))},[selected,token]);
  const compareDoc=async()=>{if(!doc){setMessage("Select a processed document first.");return}try{setComparison(await api(`/gis/compare/${doc}`,token))}catch(e){setMessage(e.message)}};
  const importGeo=async(e)=>{if(!e.target.files[0])return;const body=new FormData();body.append("file",e.target.files[0]);try{const d=await api("/gis/import",token,{method:"POST",body});setMessage(`${d.imported} parcels imported.`);const x=await api("/gis/parcels",token);setParcels(x.parcels||[])}catch(err){setMessage(err.message)}};
  return <section className="card"><div className="section-title"><div><h2>GIS / cadastral</h2><p>Survey-linked demo geometry with document-to-parcel comparison.</p></div></div><div className="options"><label>Survey parcel<select value={selected} onChange={e=>setSelected(e.target.value)}>{parcels.map(p=><option key={p.survey_number} value={p.survey_number}>{p.survey_number} — {p.village}</option>)}</select></label><label>Processed document<select value={doc} onChange={e=>setDoc(e.target.value)}><option value="">Choose document</option>{documents.map(d=><option key={d.document_id} value={d.document_id}>{d.document_id}</option>)}</select></label></div>{parcel&&<div className="gis"><Parcel parcel={parcel}/><div className="read-grid"><div><span>Parcel</span><strong>{parcel.parcel_id}</strong></div><div><span>Area</span><strong>{parcel.area}</strong></div><div><span>District</span><strong>{parcel.district}</strong></div><div><span>Source</span><strong>{parcel.source}</strong></div></div></div>}<div className="actions"><button className="secondary" onClick={compareDoc}>Compare Selected Document</button>{user.role==="admin"&&<label className="file-button">Import GeoJSON<input type="file" accept=".geojson,.json" onChange={importGeo}/></label>}</div>{comparison&&<div className={`callout ${comparison.area_match ? "success-callout" : "warning-callout"}`}><strong>Document-to-parcel comparison</strong><span>Survey {comparison.survey_number || "—"} · area {comparison.area_match ? "matches" : "does not match"} the parcel geometry record.</span></div>}{message&&<div className="info">{message}</div>}</section>;
}

function Parcel({ parcel }) { const c=parcel.geometry?.coordinates?.[0]||[]; if(!c.length)return <div className="empty">No geometry available.</div>; const xs=c.map(p=>p[0]),ys=c.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys); const pts=c.map(([x,y])=>`${40+(x-minX)/Math.max(maxX-minX,.0001)*440},${240-(y-minY)/Math.max(maxY-minY,.0001)*190}`).join(" "); return <div className="map"><svg viewBox="0 0 520 280"><defs><linearGradient id="parcelFill" x1="0" x2="1"><stop offset="0%"/><stop offset="100%"/></linearGradient></defs><rect width="520" height="280" className="map-bg"/><polygon points={pts} className="parcel"/><text x="260" y="145" textAnchor="middle">{parcel.survey_number}</text><text x="260" y="170" textAnchor="middle">{parcel.area}</text></svg></div>; }

function Integrations({ token }) { const [items,setItems]=useState([]),[docs,setDocs]=useState([]),[logs,setLogs]=useState([]),[doc,setDoc]=useState(""),[message,setMessage]=useState(""); const refresh=async()=>{try{const [a,b,c]=await Promise.all([api("/integrations/status",token),api("/documents",token),api("/integrations/logs",token)]);setItems(a.integrations||[]);setDocs(b.documents||[]);setLogs(c.logs||[]);if(!doc&&b.documents?.[0])setDoc(b.documents[0].document_id)}catch(e){setMessage(e.message)}}; useEffect(()=>{refresh()},[token]); const run=async(kind)=>{if(!doc){setMessage("Select a processed document first.");return}try{const d=await api(`${kind==="lrms"?"/integrations/lrms/sync":"/integrations/dilrmp/export"}/${doc}`,token,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});setMessage(`${d.adapter}: ${d.mode} / ${d.status}`);refresh()}catch(e){setMessage(e.message)}}; return <section className="card"><div className="section-title"><div><h2>Integration hub</h2><p>Prototype adapters are explicit about mock vs configured live endpoints.</p></div></div>{items.map(i=><div className="integration" key={i.name}><div><strong>{i.name}</strong><p>{i.description}</p></div><span className="status success">{i.mode}{i.endpoint_configured?" · configured":" · demo"}</span></div>)}<label>Processed document<select value={doc} onChange={e=>setDoc(e.target.value)}><option value="">Choose document</option>{docs.map(d=><option key={d.document_id} value={d.document_id}>{d.document_id} — {d.original_filename}</option>)}</select></label><div className="actions"><button className="secondary" onClick={()=>run("lrms")}>LRMS Sync</button><button className="secondary" onClick={()=>run("dilrmp")}>DILRMP Export</button></div>{message&&<div className="info">{message}</div>}<h3>Recent integration logs</h3><div className="table"><table><thead><tr><th>Integration</th><th>Action</th><th>Status</th><th>Document</th></tr></thead><tbody>{logs.map(l=><tr key={l.id}><td>{l.integration_name}</td><td>{l.action}</td><td>{l.status}</td><td>{l.document_id||"—"}</td></tr>)}</tbody></table></div></section>; }

function Learning({ token }) { const [feedback,setFeedback]=useState([]),[suggestions,setSuggestions]=useState({}),[error,setError]=useState(""); useEffect(()=>{Promise.all([api("/learning/feedback",token),api("/learning/suggestions",token)]).then(([a,b])=>{setFeedback(a.feedback||[]);setSuggestions(b.learned_corrections||{})}).catch(e=>setError(e.message))},[token]); return <section className="card"><div className="section-title"><div><h2>AI feedback loop</h2><p>Human corrections are retained as labelled feedback; this prototype does not silently retrain models.</p></div></div>{error&&<div className="error">{error}</div>}<div className="grid-2"><ListCard title="Correction categories" data={Object.fromEntries(Object.entries(suggestions).map(([k,v])=>[k,v.length]))} /><div className="card nested"><h3>Recent corrections</h3>{feedback.length?feedback.slice(0,10).map(r=><div className="audit" key={r.id}><b>{pretty(r.field_name)}</b><span>{r.original_value||"—"} → {r.corrected_value}</span><small>{r.actor_email}</small></div>):<div className="empty">No corrections recorded yet.</div>}</div></div></section>; }

function Users({ token }) { const [users,setUsers]=useState([]),[form,setForm]=useState({email:"",name:"",role:"citizen",password:""}),[message,setMessage]=useState(""); const load=()=>api("/admin/users",token).then(d=>setUsers(d.users||[])).catch(e=>setMessage(e.message)); useEffect(()=>{load()},[token]); const create=async()=>{try{await api("/admin/users",token,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(form)});setMessage("User created.");setForm({email:"",name:"",role:"citizen",password:""});load()}catch(e){setMessage(e.message)}}; const exportSystem=async()=>{try{const d=await api("/admin/system-export",token);const blob=new Blob([JSON.stringify(d,null,2)],{type:"application/json"});const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download="landverify-system-export.json";a.click();URL.revokeObjectURL(u)}catch(e){setMessage(e.message)}}; return <section className="card"><div className="section-title"><div><h2>User & role management</h2><p>Create controlled demo identities for Citizen, Officer and Admin workflows.</p></div><button className="secondary" onClick={exportSystem}>Export System Snapshot</button></div><div className="grid-2"><div className="card nested form-card"><h3>Create user</h3>{["email","name","password"].map(k=><input key={k} placeholder={pretty(k)} type={k==="password"?"password":"text"} value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})}/>)}<select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option value="citizen">Citizen</option><option value="officer">Officer</option><option value="admin">Admin</option></select><button className="primary" onClick={create}>Create User</button>{message&&<div className="info">{message}</div>}</div><div className="card nested"><h3>Current users</h3>{users.map(u=><div className="record-line" key={u.email}><strong>{u.email}</strong><span>{u.name}</span><span className="status">{u.role}</span></div>)}</div></div></section>; }

function APIConsole({ token }) { const [data,setData]=useState(null),[error,setError]=useState(""); useEffect(()=>{api("/api/endpoints",token).then(setData).catch(e=>setError(e.message))},[token]); if(error)return <div className="error">{error}</div>; return <section className="card"><div className="section-title"><div><h2>Live API endpoints</h2><p>The frontend is backed by a FastAPI service. Open the interactive Swagger console for request/response testing.</p></div><a className="primary-link" href={`${API}/docs`} target="_blank" rel="noreferrer">Open Swagger ↗</a></div><div className="endpoint-list">{(data?.endpoints||[]).map((e)=>{const cls=e.method.toLowerCase();return <div className="endpoint" key={`${e.method}-${e.path}`}><span className={`method ${cls}`}>{e.method}</span><code>{e.path}</code><span className="endpoint-desc">{e.description}</span><span className="role-tags">{e.roles.map(r=><em key={r}>{r}</em>)}</span></div>})}</div></section>; }

function Processing({ title, text }) { return <section className="card processing"><div className="loader"/><h2>{title}</h2><p>{text}</p></section>; }
function Redirect({ text, onGo }) { return <section className="card empty"><strong>{text}</strong><button className="primary" onClick={onGo}>Back to Dashboard</button></section>; }

createRoot(document.getElementById("root")).render(<App />);
