/**
 * Format file size from bytes to human-readable string.
 * NOTE: This function is also exported from DocumentGrid.jsx (god component pattern).
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${units[i]}`;
}

/**
 * Get file type category from MIME type.
 */
export function getFileTypeCategory(mimeType) {
  if (!mimeType) return 'unknown';
  
  if (mimeType === 'application/pdf') return 'pdf';
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('text/')) return 'text';
  
  return 'other';
}

/**
 * Get display-friendly file type label.
 */
export function getFileTypeLabel(mimeType) {
  const mapping = {
    'application/pdf': 'PDF',
    'image/jpeg': 'JPEG Image',
    'image/png': 'PNG Image',
    'image/gif': 'GIF Image',
    'text/plain': 'Text File',
  };
  
  return mapping[mimeType] || mimeType || 'Unknown';
}

/**
 * Get file extension from filename.
 */
export function getFileExtension(filename) {
  if (!filename) return '';
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

/**
 * Check if a file type is previewable.
 */
export function isPreviewable(mimeType) {
  const previewableTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'];
  return previewableTypes.includes(mimeType);
}
