import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, User, LogOut, Cpu, Activity, ChevronDown } from 'lucide-react';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="enterprise-navbar">
      <div className="navbar-left">
        <Link to="/dashboard" className="brand-logo-group">
          <div className="logo-icon-glow">
            <Cpu className="brand-icon" />
          </div>
          <div className="brand-text-container">
            <span className="brand-title">Enterprise AI</span>
            <span className="brand-subtitle">Research Engine</span>
          </div>
        </Link>
        <div className="system-status-pill">
          <Activity className="pulse-icon" />
          <span>PostgreSQL & Auth Active</span>
        </div>
      </div>

      <div className="navbar-right">
        {user && (
          <div className="user-profile-menu">
            <button
              className="profile-trigger-button"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <div className="avatar-circle">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
              </div>
              <div className="user-info-meta">
                <span className="user-name">{user.full_name || user.username}</span>
                <span className="user-role-tag">{user.role}</span>
              </div>
              <ChevronDown className={`chevron-icon ${dropdownOpen ? 'open' : ''}`} />
            </button>

            {dropdownOpen && (
              <div className="profile-dropdown-menu">
                <div className="dropdown-header">
                  <p className="user-email">{user.email}</p>
                  <p className="user-id">ID: {user.id ? `${user.id.substring(0, 8)}...` : ''}</p>
                </div>
                <div className="dropdown-divider"></div>
                <Link
                  to="/profile"
                  className="dropdown-item"
                  onClick={() => setDropdownOpen(false)}
                >
                  <User className="item-icon" />
                  <span>User Profile & Settings</span>
                </Link>
                <button
                  className="dropdown-item logout-item"
                  onClick={() => {
                    setDropdownOpen(false);
                    handleLogout();
                  }}
                >
                  <LogOut className="item-icon" />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
