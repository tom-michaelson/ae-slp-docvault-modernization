import React, { Component } from 'react';
// PreviewPanel is a class component — NOT migrated to functional (FR-016)
import { Document, Page, pdfjs } from 'react-pdf';
import { getPreviewUrl } from '../utils/api';
// Importing formatFileSize from DocumentGrid (god component dependency)
import { formatFileSize } from './DocumentGrid';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const panelStyle = {
  flex: 1,
  padding: '16px',
  backgroundColor: '#f5f5f5',
  borderLeft: '1px solid #e0e0e0',
  overflow: 'auto',
};

const emptyStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  color: '#999',
  fontSize: '14px',
};

const headerStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '12px',
};

const titleStyle = {
  fontSize: '16px',
  fontWeight: '600',
  color: '#1a1a2e',
};

const closeButtonStyle = {
  padding: '4px 8px',
  backgroundColor: 'transparent',
  border: '1px solid #ccc',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '12px',
};

const imageStyle = {
  maxWidth: '100%',
  maxHeight: '500px',
  objectFit: 'contain',
};

const metaStyle = {
  fontSize: '12px',
  color: '#666',
  margin: '4px 0',
};

class PreviewPanel extends Component {
  constructor(props) {
    super(props);
    this.state = {
      numPages: null,
      pageNumber: 1,
      loading: true,
      error: null,
    };
  }

  onDocumentLoadSuccess = ({ numPages }) => {
    this.setState({ numPages, loading: false });
  };

  onDocumentLoadError = (error) => {
    this.setState({ error: error.message, loading: false });
  };

  render() {
    const { document, onClose } = this.props;
    const { numPages, pageNumber, loading, error } = this.state;

    if (!document) {
      return (
        <div style={panelStyle}>
          <div style={emptyStyle}>Select a document to preview</div>
        </div>
      );
    }

    const previewUrl = getPreviewUrl(document.id);
    const isPdf = document.file_type === 'application/pdf';
    const isImage = document.file_type?.startsWith('image/');

    return (
      <div style={panelStyle}>
        <div style={headerStyle}>
          <span style={titleStyle}>{document.name}</span>
          <button style={closeButtonStyle} onClick={onClose}>
            ✕ Close
          </button>
        </div>
        <p style={metaStyle}>Type: {document.file_type}</p>
        {document.file_size && (
          <p style={metaStyle}>Size: {formatFileSize(document.file_size)}</p>
        )}

        {isPdf && (
          <div>
            {loading && <p>Loading PDF...</p>}
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            <Document
              file={previewUrl}
              onLoadSuccess={this.onDocumentLoadSuccess}
              onLoadError={this.onDocumentLoadError}
            >
              <Page pageNumber={pageNumber} width={400} />
            </Document>
            {numPages && (
              <p style={metaStyle}>
                Page {pageNumber} of {numPages}
              </p>
            )}
          </div>
        )}

        {isImage && (
          <div>
            <img src={previewUrl} alt={document.name} style={imageStyle} />
          </div>
        )}

        {!isPdf && !isImage && (
          <p style={metaStyle}>Preview not available for this file type.</p>
        )}
      </div>
    );
  }
}

export default PreviewPanel;
