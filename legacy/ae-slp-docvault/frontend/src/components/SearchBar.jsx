import React, { useState } from 'react';

const containerStyle = {
  display: 'flex',
  gap: '8px',
  padding: '12px 0',
};

const inputStyle = {
  flex: 1,
  padding: '8px 12px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '14px',
  outline: 'none',
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#0f3460',
  color: '#ffffff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
};

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onSearch) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={containerStyle}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search documents..."
        style={inputStyle}
      />
      <button type="submit" style={buttonStyle}>
        Search
      </button>
    </form>
  );
}

export default SearchBar;
