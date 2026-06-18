/**
 * Date formatting helper (DUPLICATE of src/utils/formatDate.js)
 * 
 * This file exists in src/lib/ with a slightly different implementation
 * than the identical-purpose file in src/utils/formatDate.js.
 * Constitution Principle V — duplicate utility directories.
 */

/**
 * Format a date to a human-readable string.
 * Slightly different format than utils/formatDate.js — uses ISO-style date.
 */
export function formatDate(dateInput) {
  if (!dateInput) return 'N/A';
  
  const date = new Date(dateInput);
  
  if (isNaN(date.getTime())) {
    return 'Invalid';
  }
  
  // Different format: YYYY-MM-DD HH:mm (vs utils version which uses toLocaleDateString)
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

/**
 * Format a date as relative time.
 * Slightly different thresholds than utils version.
 */
export function timeAgo(dateInput) {
  if (!dateInput) return '';
  
  const date = new Date(dateInput);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  
  return formatDate(dateInput);
}

export default formatDate;
