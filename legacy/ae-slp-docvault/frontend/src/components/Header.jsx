import React from 'react';

const headerStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '12px 24px',
  backgroundColor: '#1a1a2e',
  color: '#ffffff',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
};

const titleStyle = {
  fontSize: '20px',
  fontWeight: 'bold',
  margin: 0,
};

const navStyle = {
  display: 'flex',
  gap: '16px',
  alignItems: 'center',
};

const navLinkStyle = {
  color: '#a0a0b0',
  textDecoration: 'none',
  fontSize: '14px',
  cursor: 'pointer',
};

function Header({ onNavigate }) {
  return (
    <header style={headerStyle}>
      <h1 style={titleStyle}>📄 DocVault</h1>
      <nav style={navStyle}>
        <span style={navLinkStyle} onClick={() => onNavigate && onNavigate('documents')}>
          Documents
        </span>
        <span style={navLinkStyle} onClick={() => onNavigate && onNavigate('upload')}>
          Upload
        </span>
        <span style={navLinkStyle} onClick={() => onNavigate && onNavigate('search')}>
          Search
        </span>
      </nav>
    </header>
  );
}

export default Header;
