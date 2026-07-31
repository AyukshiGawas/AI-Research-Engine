import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, User, Mail, Eye, EyeOff, Cpu, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const passwordRules = [
    { label: 'At least 12 characters', valid: formData.password.length >= 12 },
    { label: 'One uppercase letter (A-Z)', valid: /[A-Z]/.test(formData.password) },
    { label: 'One lowercase letter (a-z)', valid: /[a-z]/.test(formData.password) },
    { label: 'One digit (0-9)', valid: /\d/.test(formData.password) },
    { label: 'One special character (!@#$%^&*)', valid: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.password) },
  ];

  const isPasswordValid = passwordRules.every((rule) => rule.valid);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!isPasswordValid) {
      setErrorMessage('Password does not meet all complexity requirements.');
      return;
    }

    setLoading(true);
    try {
      await register(formData);
      navigate('/login', {
        state: { message: 'Account created successfully! Please sign in.' },
      });
    } catch (err) {
      setErrorMessage(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-container">
      <div className="auth-card-wrapper glassmorphic-card register-card">
        <div className="auth-header">
          <div className="auth-logo-badge">
            <Cpu className="auth-logo-icon" />
          </div>
          <h2 className="auth-title">Create Account</h2>
          <p className="auth-subtitle">Register for the Enterprise AI Research Engine</p>
        </div>

        {errorMessage && (
          <div className="auth-alert-box error">
            <AlertCircle className="alert-icon" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <div className="input-input-wrapper">
                <User className="field-icon" />
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="johndoe"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <div className="input-input-wrapper">
                <Mail className="field-icon" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="user@enterprise.com"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="full_name">Full Name (Optional)</label>
            <div className="input-input-wrapper">
              <User className="field-icon" />
              <input
                id="full_name"
                name="full_name"
                type="text"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="John Doe"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-input-wrapper">
              <Lock className="field-icon" />
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••••••"
                required
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Password Complexity Validation Feedback Box */}
          <div className="password-checklist-box">
            <span className="checklist-title">Password Requirements:</span>
            <ul className="checklist-items">
              {passwordRules.map((rule, idx) => (
                <li key={idx} className={`checklist-item ${rule.valid ? 'valid' : ''}`}>
                  {rule.valid ? (
                    <CheckCircle className="check-icon" size={14} />
                  ) : (
                    <XCircle className="cross-icon" size={14} />
                  )}
                  <span>{rule.label}</span>
                </li>
              ))}
            </ul>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={loading || !isPasswordValid}
          >
            {loading ? (
              <span className="btn-loading">
                <span className="spinner"></span> Registering Account...
              </span>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
