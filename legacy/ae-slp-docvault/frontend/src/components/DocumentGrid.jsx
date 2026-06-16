import React, { Component } from 'react';
// DocumentGrid.jsx — ~800 line "god component" (class, NOT migrated)
// Contains: API calls, local state management, CSS-in-JS styles, and an exported utility
// This deliberately violates separation of concerns (FR-014 / Constitution Principle V)

import { fetchDocuments, searchDocuments, uploadDocument, updateTags } from '../utils/api';
import { formatDate } from '../utils/formatDate';
import { getFileTypeLabel, isPreviewable } from '../utils/fileHelpers';
// Duplicate imports from lib/ directory (Constitution Principle V)
// These are imported but only used in specific edge cases or not at all,
// demonstrating the coexistence of both utility directories without compile errors.
import { formatDate as libFormatDate } from '../lib/formatDate';
import { humanFileSize, categorizeFile } from '../lib/fileHelpers';
import { getDocuments as libGetDocuments } from '../lib/apiClient';

// ============================================================
// EXPORTED UTILITY FUNCTION (anti-pattern: exported from a component file)
// This function is imported by DocumentCard.jsx and PreviewPanel.jsx,
// creating a dependency on this 800-line god component for a 5-line utility.
// ============================================================
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${units[i]}`;
}

// ============================================================
// CSS-IN-JS STYLES (anti-pattern: styles embedded in component file)
// Should be in a separate CSS/SCSS file or styled-components
// ============================================================
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    padding: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    paddingBottom: '12px',
    borderBottom: '1px solid #e0e0e0',
  },
  title: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1a1a2e',
    margin: 0,
  },
  subtitle: {
    fontSize: '13px',
    color: '#666',
    margin: '4px 0 0 0',
  },
  controls: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  searchInput: {
    padding: '6px 10px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '13px',
    width: '200px',
  },
  filterSelect: {
    padding: '6px 10px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '13px',
    backgroundColor: '#fff',
  },
  viewToggle: {
    padding: '6px 10px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '13px',
    cursor: 'pointer',
    backgroundColor: '#fff',
  },
  viewToggleActive: {
    padding: '6px 10px',
    border: '1px solid #0f3460',
    borderRadius: '4px',
    fontSize: '13px',
    cursor: 'pointer',
    backgroundColor: '#0f3460',
    color: '#fff',
  },
  refreshButton: {
    padding: '6px 12px',
    backgroundColor: '#0f3460',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '16px',
    overflow: 'auto',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    overflow: 'auto',
  },
  card: {
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    padding: '16px',
    backgroundColor: '#ffffff',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.1s',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  cardSelected: {
    border: '2px solid #0f3460',
    borderRadius: '8px',
    padding: '15px',
    backgroundColor: '#f0f4ff',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.1s',
    boxShadow: '0 2px 8px rgba(15,52,96,0.2)',
  },
  cardTitle: {
    fontSize: '15px',
    fontWeight: '600',
    margin: '0 0 6px 0',
    color: '#1a1a2e',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  cardMeta: {
    fontSize: '12px',
    color: '#666',
    margin: '2px 0',
  },
  cardTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    marginTop: '8px',
  },
  tag: {
    fontSize: '11px',
    padding: '2px 8px',
    backgroundColor: '#e8eaf6',
    borderRadius: '12px',
    color: '#3949ab',
  },
  noTags: {
    fontSize: '12px',
    color: '#999',
    fontStyle: 'italic',
    marginTop: '8px',
  },
  listRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 12px',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    gap: '16px',
  },
  listRowSelected: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 12px',
    border: '2px solid #0f3460',
    borderRadius: '4px',
    backgroundColor: '#f0f4ff',
    cursor: 'pointer',
    gap: '16px',
  },
  listIcon: {
    fontSize: '24px',
    width: '32px',
    textAlign: 'center',
  },
  listInfo: {
    flex: 1,
  },
  listName: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#1a1a2e',
  },
  listMeta: {
    fontSize: '12px',
    color: '#888',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px',
    color: '#999',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '12px',
  },
  emptyText: {
    fontSize: '16px',
    marginBottom: '4px',
  },
  emptyHint: {
    fontSize: '13px',
    color: '#bbb',
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px',
  },
  loadingText: {
    fontSize: '14px',
    color: '#666',
  },
  errorContainer: {
    padding: '16px',
    backgroundColor: '#fff3f3',
    border: '1px solid #ffcdd2',
    borderRadius: '8px',
    margin: '16px 0',
  },
  errorText: {
    color: '#c62828',
    fontSize: '14px',
    margin: 0,
  },
  errorRetry: {
    padding: '6px 12px',
    backgroundColor: '#c62828',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
    marginTop: '8px',
  },
  statusBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    fontSize: '12px',
    color: '#888',
    borderTop: '1px solid #e0e0e0',
    marginTop: 'auto',
  },
  tagEditorOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  tagEditorModal: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '24px',
    width: '400px',
    maxWidth: '90vw',
    boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
  },
  tagEditorTitle: {
    fontSize: '16px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1a1a2e',
  },
  tagInputRow: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
  },
  tagInput: {
    flex: 1,
    padding: '8px 10px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '13px',
  },
  tagAddButton: {
    padding: '8px 12px',
    backgroundColor: '#4caf50',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  tagList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    marginBottom: '16px',
  },
  tagRemovable: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '3px 8px',
    backgroundColor: '#e8eaf6',
    borderRadius: '12px',
    fontSize: '12px',
    color: '#3949ab',
  },
  tagRemoveX: {
    cursor: 'pointer',
    color: '#e53935',
    fontWeight: 'bold',
    fontSize: '14px',
    marginLeft: '2px',
  },
  tagEditorActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '8px',
  },
  tagSaveButton: {
    padding: '8px 16px',
    backgroundColor: '#0f3460',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  tagCancelButton: {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    color: '#666',
    border: '1px solid #ccc',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  uploadArea: {
    border: '2px dashed #ccc',
    borderRadius: '8px',
    padding: '24px',
    textAlign: 'center',
    marginBottom: '16px',
    backgroundColor: '#fafafa',
    cursor: 'pointer',
    transition: 'border-color 0.2s',
  },
  uploadAreaActive: {
    border: '2px dashed #0f3460',
    borderRadius: '8px',
    padding: '24px',
    textAlign: 'center',
    marginBottom: '16px',
    backgroundColor: '#f0f4ff',
    cursor: 'pointer',
  },
  uploadIcon: {
    fontSize: '36px',
    marginBottom: '8px',
    display: 'block',
  },
  uploadText: {
    fontSize: '14px',
    color: '#666',
  },
  uploadHint: {
    fontSize: '12px',
    color: '#999',
    marginTop: '4px',
  },
  // This block of styles duplicates some styles above — intentional sloppiness
  documentPreviewLink: {
    fontSize: '12px',
    color: '#0f3460',
    textDecoration: 'underline',
    cursor: 'pointer',
    marginTop: '4px',
    display: 'inline-block',
  },
  actionButton: {
    padding: '4px 8px',
    fontSize: '11px',
    border: '1px solid #ccc',
    borderRadius: '3px',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    marginLeft: '4px',
  },
  sortIndicator: {
    fontSize: '10px',
    marginLeft: '2px',
    color: '#888',
  },
  // Abandoned feature: batch operations toolbar
  // batchToolbar: {
  //   display: 'flex',
  //   gap: '8px',
  //   padding: '8px 12px',
  //   backgroundColor: '#e3f2fd',
  //   borderRadius: '4px',
  //   marginBottom: '12px',
  //   alignItems: 'center',
  // },
  // batchCount: {
  //   fontSize: '13px',
  //   fontWeight: '500',
  //   color: '#1565c0',
  // },
  // batchAction: {
  //   padding: '4px 10px',
  //   fontSize: '12px',
  //   backgroundColor: '#1565c0',
  //   color: '#fff',
  //   border: 'none',
  //   borderRadius: '3px',
  //   cursor: 'pointer',
  // },
  // batchCancel: {
  //   padding: '4px 10px',
  //   fontSize: '12px',
  //   backgroundColor: 'transparent',
  //   color: '#666',
  //   border: '1px solid #ccc',
  //   borderRadius: '3px',
  //   cursor: 'pointer',
  //   marginLeft: 'auto',
  // },
};

// ============================================================
// HELPER FUNCTIONS (should be in separate utility files)
// ============================================================

function getFileIcon(fileType) {
  switch (fileType) {
    case 'application/pdf':
      return '📄';
    case 'image/jpeg':
    case 'image/png':
    case 'image/gif':
      return '🖼️';
    default:
      return '📎';
  }
}

function sortDocuments(docs, sortBy) {
  const sorted = [...docs];
  switch (sortBy) {
    case 'name':
      sorted.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'type':
      sorted.sort((a, b) => a.file_type.localeCompare(b.file_type));
      break;
    case 'date':
    default:
      sorted.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      break;
  }
  return sorted;
}

function filterDocuments(docs, filters) {
  let filtered = [...docs];
  if (filters.fileType) {
    filtered = filtered.filter((d) => d.file_type === filters.fileType);
  }
  if (filters.searchQuery) {
    const query = filters.searchQuery.toLowerCase();
    filtered = filtered.filter(
      (d) =>
        d.name.toLowerCase().includes(query) ||
        (d.tags && d.tags.some((t) => t.toLowerCase().includes(query)))
    );
  }
  return filtered;
}

// ============================================================
// DOCUMENT GRID COMPONENT (class component — NOT migrated)
// This is the "god component" that does everything:
// - Fetches data from API
// - Manages local state for documents, selection, filters, tags, uploads
// - Contains inline CSS-in-JS styles (above)
// - Exports a utility function (formatFileSize) used by other components
// - Handles drag-and-drop uploads
// - Contains a built-in tag editor modal
// ============================================================
class DocumentGrid extends Component {
  constructor(props) {
    super(props);
    this.state = {
      documents: [],
      loading: true,
      error: null,
      selectedDocument: null,
      viewMode: 'grid', // 'grid' or 'list'
      sortBy: 'date',
      filters: {
        fileType: '',
        searchQuery: '',
      },
      // Tag editor state (should be in its own component)
      tagEditorVisible: false,
      tagEditorDocId: null,
      tagEditorTags: [],
      tagEditorInput: '',
      tagSaving: false,
      // Upload state (duplicated from UploadButton)
      isDragging: false,
      uploadProgress: null,
      uploadError: null,
      // Batch selection (abandoned feature — state kept but never used)
      batchSelected: [],
      batchMode: false,
    };
    this.fileInputRef = React.createRef();
    this.dropZoneRef = React.createRef();
  }

  componentDidMount() {
    this.loadDocuments();
  }

  // ============================================================
  // DATA FETCHING (should be in a service or hook)
  // ============================================================
  async loadDocuments() {
    this.setState({ loading: true, error: null });
    try {
      const response = await fetchDocuments();
      this.setState({
        documents: response.data.documents || [],
        loading: false,
      });
    } catch (err) {
      this.setState({
        error: err.response?.data?.error || 'Failed to load documents',
        loading: false,
      });
    }
  }

  async handleSearch(query) {
    if (!query.trim()) {
      this.loadDocuments();
      return;
    }
    this.setState({ loading: true, error: null });
    try {
      const response = await searchDocuments(query);
      this.setState({
        documents: response.data.results || [],
        loading: false,
      });
    } catch (err) {
      this.setState({
        error: err.response?.data?.error || 'Search failed',
        loading: false,
      });
    }
  }

  // ============================================================
  // EVENT HANDLERS
  // ============================================================
  handleDocumentClick = (doc) => {
    this.setState({ selectedDocument: doc });
    if (this.props.onDocumentSelect) {
      this.props.onDocumentSelect(doc);
    }
  };

  handleSortChange = (sortBy) => {
    this.setState({ sortBy });
  };

  handleFilterChange = (filterUpdate) => {
    this.setState((prevState) => ({
      filters: { ...prevState.filters, ...filterUpdate },
    }));
  };

  handleViewToggle = () => {
    this.setState((prevState) => ({
      viewMode: prevState.viewMode === 'grid' ? 'list' : 'grid',
    }));
  };

  handleRefresh = () => {
    this.loadDocuments();
  };

  // ============================================================
  // TAG EDITOR (should be in TagEditor component, not here)
  // ============================================================
  handleOpenTagEditor = (e, doc) => {
    e.stopPropagation();
    this.setState({
      tagEditorVisible: true,
      tagEditorDocId: doc.id,
      tagEditorTags: doc.tags ? [...doc.tags] : [],
      tagEditorInput: '',
    });
  };

  handleCloseTagEditor = () => {
    this.setState({
      tagEditorVisible: false,
      tagEditorDocId: null,
      tagEditorTags: [],
      tagEditorInput: '',
    });
  };

  handleTagInputChange = (e) => {
    this.setState({ tagEditorInput: e.target.value });
  };

  handleAddTag = () => {
    const { tagEditorInput, tagEditorTags } = this.state;
    const newTag = tagEditorInput.trim();
    if (newTag && !tagEditorTags.includes(newTag) && tagEditorTags.length < 10) {
      this.setState({
        tagEditorTags: [...tagEditorTags, newTag],
        tagEditorInput: '',
      });
    }
  };

  handleRemoveTag = (tagToRemove) => {
    this.setState((prevState) => ({
      tagEditorTags: prevState.tagEditorTags.filter((t) => t !== tagToRemove),
    }));
  };

  handleTagKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      this.handleAddTag();
    }
  };

  handleSaveTags = async () => {
    const { tagEditorDocId, tagEditorTags } = this.state;
    this.setState({ tagSaving: true });
    try {
      await updateTags(tagEditorDocId, tagEditorTags);
      // Update local state
      this.setState((prevState) => ({
        documents: prevState.documents.map((d) =>
          d.id === tagEditorDocId ? { ...d, tags: tagEditorTags } : d
        ),
        tagSaving: false,
        tagEditorVisible: false,
      }));
    } catch (err) {
      console.error('Failed to save tags:', err);
      this.setState({ tagSaving: false });
    }
  };

  // ============================================================
  // DRAG AND DROP UPLOAD (duplicated logic from UploadButton)
  // ============================================================
  handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    this.setState({ isDragging: true });
  };

  handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    this.setState({ isDragging: false });
  };

  handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    this.setState({ isDragging: false });

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    await this.uploadFile(file);
  };

  handleFileInputClick = () => {
    this.fileInputRef.current?.click();
  };

  handleFileInputChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    await this.uploadFile(file);
    if (this.fileInputRef.current) this.fileInputRef.current.value = '';
  };

  async uploadFile(file) {
    this.setState({ uploadProgress: 'uploading', uploadError: null });
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name);
      await uploadDocument(formData);
      this.setState({ uploadProgress: 'done' });
      // Reload documents
      this.loadDocuments();
      setTimeout(() => this.setState({ uploadProgress: null }), 2000);
    } catch (err) {
      this.setState({
        uploadProgress: null,
        uploadError: err.response?.data?.error || 'Upload failed',
      });
    }
  }

  // ============================================================
  // BATCH OPERATIONS (abandoned feature — methods exist but are never called)
  // ============================================================
  // handleBatchToggle = (docId) => {
  //   this.setState(prevState => {
  //     const selected = prevState.batchSelected;
  //     if (selected.includes(docId)) {
  //       return { batchSelected: selected.filter(id => id !== docId) };
  //     }
  //     return { batchSelected: [...selected, docId] };
  //   });
  // };
  //
  // handleBatchDelete = async () => {
  //   // TODO: implement batch delete
  //   console.warn('Batch delete not implemented');
  // };
  //
  // handleBatchTag = async () => {
  //   // TODO: implement batch tagging
  //   console.warn('Batch tag not implemented');
  // };
  //
  // handleBatchExport = async () => {
  //   // TODO: implement batch export
  //   console.warn('Batch export not implemented');
  // };

  // ============================================================
  // RENDER HELPERS
  // ============================================================
  renderUploadArea() {
    const { isDragging, uploadProgress, uploadError } = this.state;

    return (
      <div
        ref={this.dropZoneRef}
        style={isDragging ? styles.uploadAreaActive : styles.uploadArea}
        onDragEnter={this.handleDragEnter}
        onDragOver={this.handleDragOver}
        onDragLeave={this.handleDragLeave}
        onDrop={this.handleDrop}
        onClick={this.handleFileInputClick}
      >
        <input
          type="file"
          ref={this.fileInputRef}
          onChange={this.handleFileInputChange}
          accept=".pdf,.jpg,.jpeg,.png"
          style={{ display: 'none' }}
        />
        <span style={styles.uploadIcon}>⬆️</span>
        <span style={styles.uploadText}>
          {uploadProgress === 'uploading'
            ? 'Uploading...'
            : uploadProgress === 'done'
            ? '✅ Upload complete!'
            : 'Drop files here or click to upload'}
        </span>
        <span style={styles.uploadHint}>PDF, JPEG, PNG</span>
        {uploadError && <p style={{ color: 'red', fontSize: '12px' }}>{uploadError}</p>}
      </div>
    );
  }

  renderTagEditor() {
    const { tagEditorVisible, tagEditorTags, tagEditorInput, tagSaving } = this.state;

    if (!tagEditorVisible) return null;

    return (
      <div style={styles.tagEditorOverlay} onClick={this.handleCloseTagEditor}>
        <div style={styles.tagEditorModal} onClick={(e) => e.stopPropagation()}>
          <div style={styles.tagEditorTitle}>Edit Tags</div>
          <div style={styles.tagInputRow}>
            <input
              type="text"
              value={tagEditorInput}
              onChange={this.handleTagInputChange}
              onKeyPress={this.handleTagKeyPress}
              placeholder="Add a tag..."
              style={styles.tagInput}
              maxLength={50}
            />
            <button onClick={this.handleAddTag} style={styles.tagAddButton}>
              Add
            </button>
          </div>
          <div style={styles.tagList}>
            {tagEditorTags.map((tag, i) => (
              <span key={i} style={styles.tagRemovable}>
                {tag}
                <span
                  style={styles.tagRemoveX}
                  onClick={() => this.handleRemoveTag(tag)}
                >
                  ×
                </span>
              </span>
            ))}
          </div>
          <div style={styles.tagEditorActions}>
            <button onClick={this.handleCloseTagEditor} style={styles.tagCancelButton}>
              Cancel
            </button>
            <button
              onClick={this.handleSaveTags}
              style={styles.tagSaveButton}
              disabled={tagSaving}
            >
              {tagSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  renderCard(doc) {
    const { selectedDocument } = this.state;
    const isSelected = selectedDocument?.id === doc.id;

    return (
      <div
        key={doc.id}
        style={isSelected ? styles.cardSelected : styles.card}
        onClick={() => this.handleDocumentClick(doc)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h3 style={styles.cardTitle}>
            {getFileIcon(doc.file_type)} {doc.name}
          </h3>
          <button
            style={styles.actionButton}
            onClick={(e) => this.handleOpenTagEditor(e, doc)}
            title="Edit tags"
          >
            🏷️
          </button>
        </div>
        <p style={styles.cardMeta}>{getFileTypeLabel(doc.file_type)}</p>
        <p style={styles.cardMeta}>{formatDate(doc.uploaded_at)}</p>
        {isPreviewable(doc.file_type) && (
          <span style={styles.documentPreviewLink}>Preview</span>
        )}
        {doc.tags && doc.tags.length > 0 ? (
          <div style={styles.cardTags}>
            {doc.tags.map((tag, i) => (
              <span key={i} style={styles.tag}>
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <p style={styles.noTags}>No tags</p>
        )}
      </div>
    );
  }

  renderListRow(doc) {
    const { selectedDocument } = this.state;
    const isSelected = selectedDocument?.id === doc.id;

    return (
      <div
        key={doc.id}
        style={isSelected ? styles.listRowSelected : styles.listRow}
        onClick={() => this.handleDocumentClick(doc)}
      >
        <span style={styles.listIcon}>{getFileIcon(doc.file_type)}</span>
        <div style={styles.listInfo}>
          <div style={styles.listName}>{doc.name}</div>
          <div style={styles.listMeta}>
            {getFileTypeLabel(doc.file_type)} · {formatDate(doc.uploaded_at)}
            {doc.tags && doc.tags.length > 0 && ` · ${doc.tags.length} tags`}
          </div>
        </div>
        <button
          style={styles.actionButton}
          onClick={(e) => this.handleOpenTagEditor(e, doc)}
          title="Edit tags"
        >
          🏷️
        </button>
      </div>
    );
  }

  renderEmpty() {
    return (
      <div style={styles.emptyState}>
        <span style={styles.emptyIcon}>📂</span>
        <p style={styles.emptyText}>No documents found</p>
        <p style={styles.emptyHint}>Upload a document to get started</p>
      </div>
    );
  }

  renderError() {
    const { error } = this.state;
    return (
      <div style={styles.errorContainer}>
        <p style={styles.errorText}>Error: {error}</p>
        <button style={styles.errorRetry} onClick={this.handleRefresh}>
          Retry
        </button>
      </div>
    );
  }

  // ============================================================
  // MAIN RENDER
  // ============================================================
  render() {
    const { documents, loading, error, viewMode, sortBy, filters } = this.state;

    // Apply filters and sorting (logic in component — should be elsewhere)
    let displayDocs = filterDocuments(documents, filters);
    displayDocs = sortDocuments(displayDocs, sortBy);

    return (
      <div style={styles.container}>
        {/* Header with controls */}
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Documents</h2>
            <p style={styles.subtitle}>
              {loading ? 'Loading...' : `${displayDocs.length} document${displayDocs.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <div style={styles.controls}>
            <input
              type="text"
              placeholder="Filter..."
              style={styles.searchInput}
              value={filters.searchQuery}
              onChange={(e) => this.handleFilterChange({ searchQuery: e.target.value })}
            />
            <select
              style={styles.filterSelect}
              value={filters.fileType}
              onChange={(e) => this.handleFilterChange({ fileType: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="application/pdf">PDF</option>
              <option value="image/jpeg">JPEG</option>
              <option value="image/png">PNG</option>
            </select>
            <button
              style={viewMode === 'grid' ? styles.viewToggleActive : styles.viewToggle}
              onClick={this.handleViewToggle}
              title={viewMode === 'grid' ? 'Switch to list' : 'Switch to grid'}
            >
              {viewMode === 'grid' ? '☰' : '⊞'}
            </button>
            <button style={styles.refreshButton} onClick={this.handleRefresh}>
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Upload area */}
        {this.renderUploadArea()}

        {/* Error state */}
        {error && this.renderError()}

        {/* Loading state */}
        {loading && (
          <div style={styles.loadingContainer}>
            <span style={styles.loadingText}>Loading documents...</span>
          </div>
        )}

        {/* Document grid/list */}
        {!loading && !error && displayDocs.length === 0 && this.renderEmpty()}

        {!loading && !error && displayDocs.length > 0 && (
          <div style={viewMode === 'grid' ? styles.grid : styles.list}>
            {displayDocs.map((doc) =>
              viewMode === 'grid' ? this.renderCard(doc) : this.renderListRow(doc)
            )}
          </div>
        )}

        {/* Tag editor modal */}
        {this.renderTagEditor()}

        {/* Status bar */}
        <div style={styles.statusBar}>
          <span>
            View: {viewMode} · Sort: {sortBy}
            {filters.fileType && ` · Filter: ${filters.fileType}`}
          </span>
          <span>{displayDocs.length} of {documents.length} documents</span>
        </div>
      </div>
    );
  }
}

export default DocumentGrid;
