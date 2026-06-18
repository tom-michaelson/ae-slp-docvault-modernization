/**
 * Format a date string or Date object to a human-readable format.
 * Used by DocumentCard and DocumentGrid components.
 */
export function formatDate(dateInput) {
  if (!dateInput) return 'Unknown date';
  
  const date = new Date(dateInput);
  
  if (isNaN(date.getTime())) {
    return 'Invalid date';
  }
  
  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };
  
  return date.toLocaleDateString('en-US', options);
}

/**
 * Format a date as a relative time string (e.g., "2 hours ago").
 */
export function formatRelativeDate(dateInput) {
  if (!dateInput) return '';
  
  const date = new Date(dateInput);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  
  return formatDate(dateInput);
}

export default formatDate;
