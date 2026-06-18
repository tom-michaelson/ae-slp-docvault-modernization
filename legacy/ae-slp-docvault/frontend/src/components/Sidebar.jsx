import React from 'react';

const sidebarStyle = {
  width: '200px',
  backgroundColor: '#16213e',
  color: '#ffffff',
  padding: '16px',
  minHeight: '100vh',
};

const navListStyle = {
  listStyle: 'none',
  padding: 0,
  margin: 0,
};

const navItemStyle = {
  padding: '10px 12px',
  marginBottom: '4px',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
  color: '#c0c0d0',
  transition: 'background-color 0.2s',
};

const navItemActiveStyle = {
  ...navItemStyle,
  backgroundColor: '#0f3460',
  color: '#ffffff',
};

function Sidebar({ activeSection, onNavigate }) {
  const sections = [
    { id: 'documents', label: '📁 All Documents' },
    { id: 'upload', label: '⬆️ Upload' },
    { id: 'search', label: '🔍 Search' },
    { id: 'tags', label: '🏷️ Tags' },
  ];

  return (
    <aside style={sidebarStyle}>
      <ul style={navListStyle}>
        {sections.map((section) => (
          <li
            key={section.id}
            style={activeSection === section.id ? navItemActiveStyle : navItemStyle}
            onClick={() => onNavigate && onNavigate(section.id)}
          >
            {section.label}
          </li>
        ))}
      </ul>
    </aside>
  );
}

export default Sidebar;
