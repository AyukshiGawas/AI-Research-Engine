import { Activity, Cpu, Server, Sparkles } from 'lucide-react';

function App() {
  return (
    <div className="app-shell">
      <header className="hero-card">
        <div>
          <p className="eyebrow">Enterprise AI Research Platform</p>
          <h1>AI Research Engine</h1>
          <p className="hero-copy">
            Phase 1 foundation scaffold with health endpoints, placeholder architecture, and local orchestration support.
          </p>
        </div>
        <div className="status-pill">
          <Activity size={16} /> Operational
        </div>
      </header>

      <main className="dashboard-grid">
        <section className="card">
          <div className="card-title">
            <Server size={18} /> System Health
          </div>
          <ul className="metric-list">
            <li>API: Ready</li>
            <li>Frontend: Ready</li>
            <li>Infrastructure placeholders: Configured</li>
          </ul>
        </section>

        <section className="card">
          <div className="card-title">
            <Cpu size={18} /> Architecture Overview
          </div>
          <p className="muted">
            Placeholder modules are in place for models, repositories, agents, tools, and sandbox components.
          </p>
        </section>

        <section className="card">
          <div className="card-title">
            <Sparkles size={18} /> Phase 1 Scope
          </div>
          <p className="muted">
            Authentication, AI execution, database integration, and business logic remain intentionally out of scope.
          </p>
        </section>
      </main>
    </div>
  );
}

export default App;
