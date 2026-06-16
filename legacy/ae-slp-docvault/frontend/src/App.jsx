import React, { Component } from 'react';
// App.jsx — class component (NOT migrated to functional — FR-016)
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import SearchBar from './components/SearchBar';
import DocumentGrid from './components/DocumentGrid';
import PreviewPanel from './components/PreviewPanel';
import LoginForm from './components/LoginForm';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { Provider } from 'react-redux';
import store from './store';
import { searchDocuments } from './utils/api';

const appStyle = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
};

const bodyStyle = {
  display: 'flex',
  flex: 1,
  overflow: 'hidden',
};

const mainStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
};

const contentStyle = {
  flex: 1,
  display: 'flex',
  overflow: 'hidden',
};

const searchContainerStyle = {
  padding: '8px 16px',
  borderBottom: '1px solid #e0e0e0',
  backgroundColor: '#fafafa',
};

class App extends Component {
  static contextType = AuthContext;

  constructor(props) {
    super(props);
    this.state = {
      activeSection: 'documents',
      selectedDocument: null,
      showPreview: false,
    };
  }

  handleNavigate = (section) => {
    this.setState({ activeSection: section });
  };

  handleDocumentSelect = (doc) => {
    this.setState({ selectedDocument: doc, showPreview: true });
  };

  handleClosePreview = () => {
    this.setState({ selectedDocument: null, showPreview: false });
  };

  handleSearch = async (query) => {
    // Delegate to DocumentGrid — this is a bit awkward but works
    this.documentGridRef?.handleSearch(query);
  };

  render() {
    const { activeSection, selectedDocument, showPreview } = this.state;
    const { isAuthenticated } = this.context;

    // Show login form if not authenticated
    if (!isAuthenticated) {
      return <LoginForm />;
    }

    return (
      <div style={appStyle}>
        <Header onNavigate={this.handleNavigate} />
        <div style={bodyStyle}>
          <Sidebar
            activeSection={activeSection}
            onNavigate={this.handleNavigate}
          />
          <div style={mainStyle}>
            <div style={searchContainerStyle}>
              <SearchBar onSearch={this.handleSearch} />
            </div>
            <div style={contentStyle}>
              <DocumentGrid
                ref={(ref) => (this.documentGridRef = ref)}
                onDocumentSelect={this.handleDocumentSelect}
              />
              {showPreview && (
                <PreviewPanel
                  document={selectedDocument}
                  onClose={this.handleClosePreview}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

// Wrap App in AuthProvider and Redux Provider
function AppWithAuth() {
  return (
    <Provider store={store}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </Provider>
  );
}

export default AppWithAuth;
