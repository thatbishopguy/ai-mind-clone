"use client";

import { useEffect, useMemo, useState } from "react";
import Decisions from "@/components/Decisions";
import { createDecision, Decision, listDecisions } from "@/lib/decisions";

const modules = [
  "Dashboard",
  "New Decision",
  "Decisions",
  "Mind Model",
  "Memories",
  "Simulator",
  "Calibration",
  "Settings",
] as const;

type Module = (typeof modules)[number];

type DraftDecision = {
  situation: string;
  domain: string;
  stakes: string;
  timePressure: string;
};

const emptyDraft: DraftDecision = {
  situation: "",
  domain: "Personal",
  stakes: "Medium",
  timePressure: "Low",
};

function Dashboard() {
  const [count, setCount] = useState<string>("Loading…");
  useEffect(() => {
    let active = true;
    listDecisions().then((items) => { if (active) setCount(String(items.length)); })
      .catch(() => { if (active) setCount("Unavailable"); });
    return () => { active = false; };
  }, []);
  const cards = [
    ["Model status", "Foundation active"],
    ["Saved decisions", count],
    ["Calibration cases", "0"],
    ["Current milestone", "M5 — AI suggestions"],
  ];

  return (
    <div className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow dark">DECISION ENGINE</p>
          <h2>Dashboard</h2>
          <p className="lede">
            Save decision context and revisit it from the Decisions screen.
          </p>
        </div>
        <span className="buildBadge">M5 BUILD</span>
      </header>

      <section className="statusGrid" aria-label="System status">
        {cards.map(([label, value]) => (
          <article className="card" key={label}>
            <span className="cardLabel">{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="eyebrow dark">NEXT ACTION</p>
            <h3>Capture the first decision</h3>
          </div>
        </div>
        <p className="muted">
          M5 adds AI context and option suggestions for review. Your criteria and rules control scoring.
        </p>
      </section>
    </div>
  );
}

function NewDecision({ onOpen }: { onOpen: (id: string) => void }) {
  const [draft, setDraft] = useState<DraftDecision>(emptyDraft);
  const [saved, setSaved] = useState<Decision | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const canAnalyze = useMemo(() => draft.situation.trim().length >= 10, [draft.situation]);

  function update<K extends keyof DraftDecision>(key: K, value: DraftDecision[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
    setSaved(null);
    setSaveError("");
  }

  async function submit() {
    if (!canAnalyze || saving || saved) return;
    setSaving(true);
    setSaveError("");
    try {
      const decision = await createDecision({
        situation: draft.situation.trim(), domain: draft.domain,
        stakes: draft.stakes, time_pressure: draft.timePressure,
      });
      setSaved(decision);
    } catch (cause) {
      setSaveError(cause instanceof Error ? cause.message : "Could not save the decision.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="pageStack">
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow dark">DECISION WORKSPACE</p>
          <h2>New Decision</h2>
          <p className="lede">Describe the situation naturally. The engine will progressively add structured analysis behind this interface.</p>
        </div>
      </header>

      <section className="workspaceGrid">
        <fieldset className="panel decisionForm" disabled={saving}>
          <label className="fieldLabel" htmlFor="situation">What&apos;s happening?</label>
          <textarea
            id="situation"
            value={draft.situation}
            onChange={(event) => update("situation", event.target.value)}
            placeholder="Explain the situation, what happened, who is involved, and what decision you need to make..."
            rows={10}
          />

          <div className="fieldGrid">
            <label>
              <span className="fieldLabel">Domain</span>
              <select value={draft.domain} onChange={(event) => update("domain", event.target.value)}>
                <option>Personal</option>
                <option>Work</option>
                <option>Relationship</option>
                <option>Financial</option>
                <option>Safety</option>
                <option>Health</option>
                <option>Other</option>
              </select>
            </label>

            <label>
              <span className="fieldLabel">Stakes</span>
              <select value={draft.stakes} onChange={(event) => update("stakes", event.target.value)}>
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
                <option>Critical</option>
              </select>
            </label>

            <label>
              <span className="fieldLabel">Time pressure</span>
              <select value={draft.timePressure} onChange={(event) => update("timePressure", event.target.value)}>
                <option>None</option>
                <option>Low</option>
                <option>Moderate</option>
                <option>High</option>
                <option>Immediate</option>
              </select>
            </label>
          </div>

          <div className="formFooter">
            <span className="helperText">Minimum 10 characters to save.</span>
            <button className="primaryButton" disabled={!canAnalyze || saving || saved !== null} onClick={submit} type="button">
              {saving ? "Saving…" : saved ? "Saved" : "Save Decision"}
            </button>
          </div>
          {saveError && <p role="alert">{saveError} Your input is still here.</p>}
        </fieldset>

        <aside className="panel contextPanel">
          <p className="eyebrow dark">CURRENT CONTEXT</p>
          <dl className="contextList">
            <div><dt>Domain</dt><dd>{draft.domain}</dd></div>
            <div><dt>Stakes</dt><dd>{draft.stakes}</dd></div>
            <div><dt>Time pressure</dt><dd>{draft.timePressure}</dd></div>
            <div><dt>Input length</dt><dd>{draft.situation.trim().length} chars</dd></div>
          </dl>

          {saved ? (
            <div className="analysisPreview" role="status">
              <span className="statusDot" />
              <div>
                <strong>Decision saved</strong>
                <p>Your decision is saved. Open it to review structured context and candidate options.</p>
                <button className="primaryButton" type="button" onClick={() => onOpen(saved.id)}>Open saved decision</button>
              </div>
            </div>
          ) : (
            <div className="emptyState">
              <strong>Analysis preview</strong>
              <p>Recommendation, options, confidence, values, risks, and logic/emotion conflict will appear here as those modules come online.</p>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
}

function Placeholder({ name }: { name: Module }) {
  return (
    <div className="pageStack">
      <header className="pageHeader">
        <div>
          <p className="eyebrow dark">PLANNED MODULE</p>
          <h2>{name}</h2>
          <p className="lede">This navigation target is reserved so the application can grow without restructuring the interface.</p>
        </div>
      </header>
      <section className="panel emptyModule">
        <span className="buildBadge">COMING LATER</span>
        <p>Module boundary established in M1.</p>
      </section>
    </div>
  );
}

export default function HomePage() {
  const [activeModule, setActiveModule] = useState<Module>("New Decision");
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    function restoreSelection() {
      const id = new URLSearchParams(window.location.search).get("decision");
      setSelectedId(id);
      if (id) setActiveModule("Decisions");
    }
    restoreSelection();
    window.addEventListener("popstate", restoreSelection);
    return () => window.removeEventListener("popstate", restoreSelection);
  }, []);

  function openDecision(id: string | null) {
    setSelectedId(id);
    setActiveModule("Decisions");
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("decision", id);
    else url.searchParams.delete("decision");
    window.history.pushState(null, "", url);
  }

  let content;
  if (activeModule === "Dashboard") content = <Dashboard />;
  else if (activeModule === "New Decision") content = <NewDecision onOpen={openDecision} />;
  else if (activeModule === "Decisions") content = <Decisions selectedId={selectedId} onSelect={openDecision} />;
  else content = <Placeholder name={activeModule} />;

  return (
    <main className="appShell">
      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="brandRow">
          <div>
            <p className="eyebrow">AI MIND CLONE</p>
            <h1>Decision Engine</h1>
          </div>
          <button className="closeMenu" onClick={() => setMenuOpen(false)} aria-label="Close navigation" type="button">×</button>
        </div>

        <nav aria-label="Primary navigation">
          {modules.map((module) => (
            <button
              className={activeModule === module ? "navItem active" : "navItem"}
              key={module}
              type="button"
              onClick={() => {
                setActiveModule(module);
                setSelectedId(null);
                const url = new URL(window.location.href);
                url.searchParams.delete("decision");
                window.history.pushState(null, "", url);
                setMenuOpen(false);
              }}
            >
              <span>{module}</span>
              {module === "New Decision" ? <span className="navPill">LIVE</span> : null}
            </button>
          ))}
        </nav>

        <div className="sidebarFooter">
          <span className="statusDot" />
          <span>Local development build</span>
        </div>
      </aside>

      <section className="mainColumn">
        <header className="mobileTopbar">
          <button className="menuButton" onClick={() => setMenuOpen(true)} type="button" aria-label="Open navigation">☰</button>
          <div>
            <strong>AI Mind Clone</strong>
            <span>{activeModule}</span>
          </div>
        </header>
        <div className="content">{content}</div>
      </section>

      {menuOpen ? <button className="scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} type="button" /> : null}
    </main>
  );
}
