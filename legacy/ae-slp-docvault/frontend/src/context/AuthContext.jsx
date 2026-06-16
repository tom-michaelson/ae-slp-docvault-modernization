import React, { createContext, Component } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

const AuthContext = createContext(null);

/**
 * AuthContext Provider (Constitution Principle I — Fractured Authentication)
 * 
 * This provider manages the JWT login flow. It:
 * 1. Calls POST /api/auth/login → gets { token, refreshToken } ✓
 * 2. Calls POST /api/auth/refresh → gets { session: {...} } ✗ (BUG)
 * 3. Tries response.data.token.split('.') → null reference → CRASH
 * 
 * The crash is caused by the backend's /refresh endpoint returning
 * a session-shaped response instead of a JWT-shaped response.
 */
class AuthProvider extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      token: null,
      loading: false,
      error: null,
      isAuthenticated: false,
    };
  }

  componentDidMount() {
    // Check if we can bypass auth
    this.checkAuthBypass();
  }

  checkAuthBypass = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      if (response.data.skipAuth) {
        this.setState({
          user: { email: 'dev@docvault.local', role: 'admin' },
          isAuthenticated: true,
        });
      }
    } catch (err) {
      // Backend not available yet — ignore
    }
  };

  login = async (email, password) => {
    this.setState({ loading: true, error: null });
    
    try {
      // Step 1: Login — this works correctly
      const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password,
      });
      
      const { token, refreshToken } = loginResponse.data;
      
      // Store the initial token
      localStorage.setItem('docvault_token', token);
      localStorage.setItem('docvault_refresh_token', refreshToken);
      
      // Step 2: Immediately refresh the token (common pattern)
      // BUG: The refresh endpoint returns { session: {...} } instead of { token: "..." }
      const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refreshToken,
      });
      
      // Step 3: CRASH — refreshResponse.data.token is undefined
      // because the backend returned { session: {...} } instead of { token: "..." }
      // This line crashes with: Cannot read properties of undefined (reading 'split')
      const parts = refreshResponse.data.token.split('.');
      const payload = JSON.parse(atob(parts[1]));
      
      this.setState({
        user: payload,
        token: refreshResponse.data.token,
        isAuthenticated: true,
        loading: false,
      });
      
      localStorage.setItem('docvault_token', refreshResponse.data.token);
    } catch (err) {
      this.setState({
        error: err.message || 'Login failed',
        loading: false,
        isAuthenticated: false,
      });
      throw err;
    }
  };

  logout = () => {
    this.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    localStorage.removeItem('docvault_token');
    localStorage.removeItem('docvault_refresh_token');
  };

  render() {
    const value = {
      user: this.state.user,
      token: this.state.token,
      loading: this.state.loading,
      error: this.state.error,
      isAuthenticated: this.state.isAuthenticated,
      login: this.login,
      logout: this.logout,
    };

    return (
      <AuthContext.Provider value={value}>
        {this.props.children}
      </AuthContext.Provider>
    );
  }
}

export { AuthContext, AuthProvider };
export default AuthContext;
