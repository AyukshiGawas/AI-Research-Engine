import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, Shield, Key, CheckCircle, AlertCircle, Calendar, Hash } from 'lucide-react';

export const ProfilePage = () => {
  const { user, updateProfile } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [updating, setUpdating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSuccessMsg('');
    setErrorMsg('');

    setUpdating(true);
    try {
      const payload = { full_name: fullName, email };
      if (password) {
        payload.password = password;
      }
      await updateProfile(payload);
      setPassword('');
      setSuccessMsg('Profile updated successfully!');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Update failed.');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="profile-page-container">
      <div className="profile-header-card glassmorphic-card">
        <div className="profile-avatar-large">
          {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.username.charAt(0).toUpperCase()}
        </div>
        <div className="profile-identity">
          <h2 className="profile-name">{user?.full_name || user?.username}</h2>
          <p className="profile-email-badge">{user?.email}</p>
          <div className="profile-tags-row">
            <span className="role-pill">{user?.role}</span>
            <span className="active-pill">Account Active</span>
          </div>
        </div>
      </div>

      <div className="profile-grid-two-col">
        {/* Profile Settings Form */}
        <div className="profile-form-card glassmorphic-card">
          <h3 className="card-section-title">Account Settings</h3>

          {successMsg && (
            <div className="auth-alert-box success">
              <CheckCircle size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {errorMsg && (
            <div className="auth-alert-box error">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleUpdate} className="profile-form">
            <div className="form-group">
              <label>Username (Read Only)</label>
              <div className="input-input-wrapper disabled">
                <User className="field-icon" />
                <input type="text" value={user?.username || ''} disabled />
              </div>
            </div>

            <div className="form-group">
              <label>Full Name</label>
              <div className="input-input-wrapper">
                <User className="field-icon" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <div className="input-input-wrapper">
                <Mail className="field-icon" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>New Password (Leave blank to keep unchanged)</label>
              <div className="input-input-wrapper">
                <Key className="field-icon" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button type="submit" className="btn-primary-glow" disabled={updating}>
              {updating ? 'Saving Changes...' : 'Save Profile Changes'}
            </button>
          </form>
        </div>

        {/* Security Details Card */}
        <div className="security-details-card glassmorphic-card">
          <h3 className="card-section-title">Security & Session Overview</h3>

          <div className="security-info-list">
            <div className="info-item">
              <div className="item-label">
                <Hash size={16} />
                <span>User UUID</span>
              </div>
              <div className="item-value monospace">{user?.id}</div>
            </div>

            <div className="info-item">
              <div className="item-label">
                <Shield size={16} />
                <span>Authentication Method</span>
              </div>
              <div className="item-value">HttpOnly Cookie + In-Memory JWT</div>
            </div>

            <div className="info-item">
              <div className="item-label">
                <Calendar size={16} />
                <span>Member Since</span>
              </div>
              <div className="item-value">
                {user?.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}
              </div>
            </div>

            <div className="info-item">
              <div className="item-label">
                <Calendar size={16} />
                <span>Last Login Timestamp</span>
              </div>
              <div className="item-value">
                {user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Just now'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
