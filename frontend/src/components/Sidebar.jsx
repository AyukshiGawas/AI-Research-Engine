import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, User, FolderKanban, ShieldCheck, FileText } from 'lucide-react';

export const Sidebar = () => {
  return (
    <aside className="enterprise-sidebar">
      <div className="sidebar-section">
        <h4 className="sidebar-section-title">Workspace Navigation</h4>
        <nav className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard className="sidebar-icon" />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/profile"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <User className="sidebar-icon" />
            <span>Account Profile</span>
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-section">
        <h4 className="sidebar-section-title">Engine Features</h4>
        <div className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className="sidebar-link"
          >
            <FolderKanban className="sidebar-icon" />
            <span>Research Workspaces</span>
            <span className="badge-pill">Phase 2</span>
          </NavLink>
          <div className="sidebar-link active-feature">
            <FileText className="sidebar-icon" />
            <span>Document Workspace</span>
            <span className="badge-pill active">Phase 3</span>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="security-badge-box">
          <ShieldCheck className="shield-icon" />
          <div className="security-info">
            <span className="sec-title">HttpOnly Cookie Auth</span>
            <span className="sec-desc">JWT + UUID DB Sessions</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
