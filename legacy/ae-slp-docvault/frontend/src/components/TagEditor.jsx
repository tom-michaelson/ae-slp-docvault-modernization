import React, { useState } from 'react';
import { updateTags } from '../utils/api';

const containerStyle = {
  padding: '12px',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  backgroundColor: '#fafafa',
};

const inputRowStyle = {
  display: 'flex',
  gap: '8px',
  marginBottom: '8px',
};

const inputStyle = {
  flex: 1,
  padding: '6px 10px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '13px',
};

const addButtonStyle = {
  padding: '6px 12px',
  backgroundColor: '#4caf50',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '13px',
};

const saveButtonStyle = {
  padding: '6px 16px',
  backgroundColor: '#0f3460',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '13px',
  marginTop: '8px',
};

const tagStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  padding: '2px 8px',
  backgroundColor: '#e8eaf6',
  borderRadius: '12px',
  fontSize: '12px',
  color: '#3949ab',
  margin: '2px',
};

const removeStyle = {
  cursor: 'pointer',
  color: '#e53935',
  fontWeight: 'bold',
  fontSize: '14px',
};

function TagEditor({ documentId, initialTags, onTagsUpdated }) {
  const [tags, setTags] = useState(initialTags || []);
  const [newTag, setNewTag] = useState('');
  const [saving, setSaving] = useState(false);

  const handleAdd = () => {
    const tag = newTag.trim();
    if (tag && !tags.includes(tag) && tags.length < 10) {
      setTags([...tags, tag]);
      setNewTag('');
    }
  };

  const handleRemove = (tagToRemove) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTags(documentId, tags);
      if (onTagsUpdated) onTagsUpdated(tags);
    } catch (err) {
      console.error('Failed to save tags:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div style={containerStyle}>
      <div style={inputRowStyle}>
        <input
          type="text"
          value={newTag}
          onChange={(e) => setNewTag(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Add a tag..."
          style={inputStyle}
          maxLength={50}
        />
        <button onClick={handleAdd} style={addButtonStyle}>
          Add
        </button>
      </div>
      <div>
        {tags.map((tag, i) => (
          <span key={i} style={tagStyle}>
            {tag}
            <span style={removeStyle} onClick={() => handleRemove(tag)}>
              ×
            </span>
          </span>
        ))}
      </div>
      <button onClick={handleSave} style={saveButtonStyle} disabled={saving}>
        {saving ? 'Saving...' : 'Save Tags'}
      </button>
    </div>
  );
}

export default TagEditor;
