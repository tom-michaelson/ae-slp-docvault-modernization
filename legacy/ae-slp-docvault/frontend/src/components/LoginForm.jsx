import React, { Component } from 'react';
// LoginForm is a class component — NOT migrated to functional (FR-016)
import { AuthContext } from '../context/AuthContext';

const formStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100vh',
  backgroundColor: '#1a1a2e',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
};

const cardStyle = {
  backgroundColor: '#ffffff',
  borderRadius: '8px',
  padding: '32px',
  width: '360px',
  boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
};

const titleStyle = {
  fontSize: '24px',
  fontWeight: '600',
  color: '#1a1a2e',
  marginBottom: '24px',
  textAlign: 'center',
};

const inputStyle = {
  width: '100%',
  padding: '10px 12px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '14px',
  marginBottom: '12px',
  boxSizing: 'border-box',
};

const buttonStyle = {
  width: '100%',
  padding: '10px',
  backgroundColor: '#0f3460',
  color: '#ffffff',
  border: 'none',
  borderRadius: '4px',
  fontSize: '14px',
  cursor: 'pointer',
  marginTop: '8px',
};

const errorStyle = {
  color: '#c62828',
  fontSize: '13px',
  marginTop: '8px',
  textAlign: 'center',
};

class LoginForm extends Component {
  static contextType = AuthContext;

  constructor(props) {
    super(props);
    this.state = {
      email: '',
      password: '',
      error: null,
    };
  }

  handleSubmit = async (e) => {
    e.preventDefault();
    const { email, password } = this.state;
    
    try {
      // This calls AuthContext.login() which will crash 
      // due to the refresh endpoint bug (FR-007)
      await this.context.login(email, password);
    } catch (err) {
      this.setState({
        error: err.message || 'Login failed. The app has crashed — check the console.',
      });
    }
  };

  render() {
    const { email, password, error } = this.state;
    const { loading } = this.context;

    return (
      <div style={formStyle}>
        <div style={cardStyle}>
          <h1 style={titleStyle}>📄 DocVault Login</h1>
          <form onSubmit={this.handleSubmit}>
            <input
              type="email"
              value={email}
              onChange={(e) => this.setState({ email: e.target.value })}
              placeholder="Email"
              style={inputStyle}
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => this.setState({ password: e.target.value })}
              placeholder="Password"
              style={inputStyle}
              required
            />
            <button type="submit" style={buttonStyle} disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          {error && <p style={errorStyle}>{error}</p>}
          {this.context.error && (
            <p style={errorStyle}>{this.context.error}</p>
          )}
        </div>
      </div>
    );
  }
}

export default LoginForm;
