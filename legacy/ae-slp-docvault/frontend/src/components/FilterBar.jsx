import React from 'react';

const containerStyle = {
  display: 'flex',
  gap: '12px',
  padding: '8px 0',
  alignItems: 'center',
  flexWrap: 'wrap',
};

const selectStyle = {
  padding: '6px 10px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '13px',
  backgroundColor: '#fff',
};

const labelStyle = {
  fontSize: '13px',
  color: '#555',
};

function FilterBar({ onFilterChange }) {
  const handleTypeChange = (e) => {
    if (onFilterChange) {
      onFilterChange({ fileType: e.target.value });
    }
  };

  const handleSortChange = (e) => {
    if (onFilterChange) {
      onFilterChange({ sortBy: e.target.value });
    }
  };

  return (
    <div style={containerStyle}>
      <span style={labelStyle}>Filter by:</span>
      <select onChange={handleTypeChange} style={selectStyle} defaultValue="">
        <option value="">All Types</option>
        <option value="application/pdf">PDF</option>
        <option value="image/jpeg">JPEG</option>
        <option value="image/png">PNG</option>
      </select>
      <span style={labelStyle}>Sort by:</span>
      <select onChange={handleSortChange} style={selectStyle} defaultValue="date">
        <option value="date">Date (newest)</option>
        <option value="name">Name</option>
        <option value="type">Type</option>
      </select>
    </div>
  );
}

export default FilterBar;
