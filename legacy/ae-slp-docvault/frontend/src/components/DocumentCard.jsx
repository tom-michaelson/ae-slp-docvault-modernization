import React from 'react';
import { formatDate } from '../utils/formatDate';
// Intentionally importing formatFileSize from DocumentGrid (god component pattern)
// This creates a dependency on the 800-line god component for a simple utility
import { formatFileSize } from './DocumentGrid';

const cardStyle = {
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  padding: '16px',
  backgroundColor: '#ffffff',
  cursor: 'pointer',
  transition: 'box-shadow 0.2s',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
};

const titleStyle = {
  fontSize: '16px',
  fontWeight: '600',
  margin: '0 0 8px 0',
  color: '#1a1a2e',
};

const metaStyle = {
  fontSize: '12px',
  color: '#666',
  margin: '4px 0',
};

const tagContainerStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '4px',
  marginTop: '8px',
};

const tagStyle = {
  fontSize: '11px',
  padding: '2px 8px',
  backgroundColor: '#e8eaf6',
  borderRadius: '12px',
  color: '#3949ab',
};

function DocumentCard({ document, onClick }) {
  const { name, file_type, tags, uploaded_at } = document;
  
  return (
    <div style={cardStyle} onClick={() => onClick && onClick(document)}>
      <h3 style={titleStyle}>{name}</h3>
      <p style={metaStyle}>Type: {file_type}</p>
      <p style={metaStyle}>Uploaded: {formatDate(uploaded_at)}</p>
      {tags && tags.length > 0 && (
        <div style={tagContainerStyle}>
          {tags.map((tag, i) => (
            <span key={i} style={tagStyle}>{tag}</span>
          ))}
        </div>
      )}
      {(!tags || tags.length === 0) && (
        <p style={{ ...metaStyle, fontStyle: 'italic' }}>No tags</p>
      )}
    </div>
  );
}

export default DocumentCard;
