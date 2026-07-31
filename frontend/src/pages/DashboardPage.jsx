import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { projectService } from '../services/projectService';
import { FolderPlus, Layers, ShieldCheck, Database, Cpu, Activity, Clock, PlusCircle } from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // New Project Form Modal state
  const [showModal, setShowModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchProjects = async () => {
    setLoadingProjects(true);
    try {
      const data = await projectService.getProjects();
      setProjects(data);
    } catch (err) {
      console.error('Error fetching projects:', err);
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!newProjectName.trim()) {
      setErrorMsg('Project name is required.');
      return;
    }

    setCreating(true);
    try {
      await projectService.createProject({
        name: newProjectName,
        description: newProjectDesc,
      });
      setNewProjectName('');
      setNewProjectDesc('');
      setShowModal(false);
      await fetchProjects();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create project workspace.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="dashboard-view-container">
      {/* Welcome Banner */}
      <div className="dashboard-welcome-banner glassmorphic-card">
        <div className="banner-text">
          <h1 className="welcome-title">
            Welcome back, {user?.full_name || user?.username}!
          </h1>
          <p className="welcome-subtitle">
            Enterprise AI Research Engine Workspace | Role: <span className="highlight-role">{user?.role}</span>
          </p>
        </div>
        <button className="btn-primary-glow" onClick={() => setShowModal(true)}>
          <FolderPlus size={18} />
          <span>New Research Workspace</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card glassmorphic-card">
          <div className="metric-header">
            <span className="metric-title">Active Database</span>
            <Database className="metric-icon cyan" />
          </div>
          <div className="metric-value">PostgreSQL 16</div>
          <div className="metric-status">SQLAlchemy + Alembic Migrations</div>
        </div>

        <div className="metric-card glassmorphic-card">
          <div className="metric-header">
            <span className="metric-title">Authentication Protocol</span>
            <ShieldCheck className="metric-icon green" />
          </div>
          <div className="metric-value">HttpOnly Cookie</div>
          <div className="metric-status">In-Memory JWT Access Token (15m)</div>
        </div>

        <div className="metric-card glassmorphic-card">
          <div className="metric-header">
            <span className="metric-title">Workspace Projects</span>
            <Layers className="metric-icon purple" />
          </div>
          <div className="metric-value">{projects.length}</div>
          <div className="metric-status">UUID Entities & Foreign Keys</div>
        </div>

        <div className="metric-card glassmorphic-card">
          <div className="metric-header">
            <span className="metric-title">Engine Uptime</span>
            <Activity className="metric-icon orange" />
          </div>
          <div className="metric-value">100% Operational</div>
          <div className="metric-status">Audit Logging Enabled</div>
        </div>
      </div>

      {/* Projects Section */}
      <div className="projects-section-container">
        <div className="section-header">
          <div>
            <h2 className="section-title">Research Workspaces</h2>
            <p className="section-subtitle">Manage multi-agent projects and dataset contexts</p>
          </div>
          <button className="btn-secondary-outline" onClick={() => setShowModal(true)}>
            <PlusCircle size={16} />
            <span>Create Workspace</span>
          </button>
        </div>

        {loadingProjects ? (
          <div className="loading-projects-skeleton">
            <div className="spinner"></div>
            <span>Loading workspaces from PostgreSQL...</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="empty-projects-card glassmorphic-card">
            <Layers className="empty-icon" size={48} />
            <h3>No Research Workspaces Yet</h3>
            <p>Create your first project workspace to start running multi-agent AI research tasks.</p>
            <button className="btn-primary-glow" onClick={() => setShowModal(true)}>
              <FolderPlus size={18} />
              <span>Create First Workspace</span>
            </button>
          </div>
        ) : (
          <div className="projects-grid">
            {projects.map((proj) => (
              <div key={proj.id} className="project-card glassmorphic-card">
                <div className="project-card-header">
                  <span className="status-badge active">{proj.status}</span>
                  <span className="project-date">
                    <Clock size={12} />
                    {new Date(proj.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 className="project-name">{proj.name}</h3>
                <p className="project-desc">{proj.description || 'No description provided.'}</p>
                <div className="project-card-footer">
                  <span className="project-id-badge">ID: {proj.id.substring(0, 8)}...</span>
                  <span className="phase-pill">Ready</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal for Creating New Workspace */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-content glassmorphic-card">
            <h3 className="modal-title">Create Research Workspace</h3>
            <p className="modal-subtitle">Define a new project context for your research team</p>

            {errorMsg && <div className="auth-alert-box error">{errorMsg}</div>}

            <form onSubmit={handleCreateProject} className="modal-form">
              <div className="form-group">
                <label>Workspace Title</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Autonomous Financial LLM Analysis"
                  required
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  rows={3}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Optional project scope summary..."
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowModal(false)}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary-glow" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
