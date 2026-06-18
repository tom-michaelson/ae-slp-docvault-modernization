import React, { useState, useRef } from 'react';
import { uploadDocument } from '../utils/api';

const containerStyle = {
  display: 'inline-block',
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#4caf50',
  color: '#ffffff',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
};

const statusStyle = {
  fontSize: '12px',
  color: '#666',
  marginTop: '4px',
};

function UploadButton({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const fileInputRef = useRef(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setStatus('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name);

      const response = await uploadDocument(formData);
      setStatus(`Uploaded: ${response.data.name}`);
      if (onUploadComplete) onUploadComplete(response.data);
    } catch (err) {
      setStatus(`Upload failed: ${err.response?.data?.error || err.message}`);
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div style={containerStyle}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf,.jpg,.jpeg,.png"
        style={{ display: 'none' }}
      />
      <button onClick={handleClick} style={buttonStyle} disabled={uploading}>
        {uploading ? 'Uploading...' : '📤 Upload Document'}
      </button>
      {status && <p style={statusStyle}>{status}</p>}
    </div>
  );
}

export default UploadButton;
