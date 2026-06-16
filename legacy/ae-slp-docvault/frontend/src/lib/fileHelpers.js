/**
 * File helper utilities (DUPLICATE of src/utils/fileHelpers.js)
 * 
 * This file exists in src/lib/ with slightly different implementations
 * than the identical-purpose file in src/utils/fileHelpers.js.
 * Constitution Principle V — duplicate utility directories.
 */

/**
 * Format bytes to human readable size.
 * Uses 1000-based units (SI) instead of 1024-based (binary) like utils version.
 */
export function humanFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 bytes';
  
  // SI units (1000) instead of binary (1024) — subtle difference from utils version
  const units = ['bytes', 'kB', 'MB', 'GB'];
  const k = 1000;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

/**
 * Get file category from MIME type.
 * Returns different labels than utils version.
 */
export function categorizeFile(mimeType) {
  if (!mimeType) return 'Unknown';
  
  const categories = {
    'application/pdf': 'Document',
    'image/jpeg': 'Photo',
    'image/png': 'Image',
    'image/gif': 'Animation',
    'text/plain': 'Text',
    'text/csv': 'Spreadsheet',
  };
  
  return categories[mimeType] || 'File';
}

/**
 * Check if file can be displayed inline.
 * Slightly different supported types than utils version.
 */
export function canPreview(mimeType) {
  const supported = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml'];
  return supported.includes(mimeType);
}

/**
 * Get icon emoji for file type.
 */
export function fileIcon(mimeType) {
  const icons = {
    'application/pdf': '📑',
    'image/jpeg': '🖼',
    'image/png': '🖼',
    'text/plain': '📝',
  };
  return icons[mimeType] || '📄';
}
