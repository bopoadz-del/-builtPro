// Date/Time and Number/Currency Formatting Utilities - ITEMS 94 & 95

// Date/Time Formatting - ITEM 94
export const formatDate = (date, options = {}) => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid Date';

  const defaults = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(d);
};

export const formatDateTime = (date, options = {}) => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid Date';

  const defaults = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };

  return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(d);
};

export const formatTime = (date, options = {}) => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid Time';

  const defaults = {
    hour: '2-digit',
    minute: '2-digit',
  };

  return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(d);
};

export const formatRelativeTime = (date) => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return 'Invalid Date';

  const now = new Date();
  const diffInSeconds = Math.floor((now - d) / 1000);

  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`;
  return `${Math.floor(diffInSeconds / 31536000)} years ago`;
};

export const formatDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) return '';
  return `${formatDate(startDate)} - ${formatDate(endDate)}`;
};

export const getDateDifference = (date1, date2, unit = 'days') => {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffInMs = Math.abs(d2 - d1);

  const units = {
    seconds: 1000,
    minutes: 1000 * 60,
    hours: 1000 * 60 * 60,
    days: 1000 * 60 * 60 * 24,
    weeks: 1000 * 60 * 60 * 24 * 7,
    months: 1000 * 60 * 60 * 24 * 30,
    years: 1000 * 60 * 60 * 24 * 365,
  };

  return Math.floor(diffInMs / units[unit]);
};

// Number/Currency Formatting - ITEM 95
export const formatCurrency = (value, currency = 'USD', options = {}) => {
  if (value === null || value === undefined) return '';

  const defaults = {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  };

  return new Intl.NumberFormat('en-US', { ...defaults, ...options }).format(value);
};

export const formatNumber = (value, options = {}) => {
  if (value === null || value === undefined) return '';

  const defaults = {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  };

  return new Intl.NumberFormat('en-US', { ...defaults, ...options }).format(value);
};

export const formatPercent = (value, decimals = 1) => {
  if (value === null || value === undefined) return '';

  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100);
};

export const formatCompactNumber = (value) => {
  if (value === null || value === undefined) return '';

  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};

export const formatFileSize = (bytes) => {
  if (bytes === null || bytes === undefined) return '';
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

export const formatOrdinal = (n) => {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

export const parseCurrency = (value) => {
  if (!value) return 0;
  return parseFloat(value.replace(/[^0-9.-]+/g, ''));
};

export const parseNumber = (value) => {
  if (!value) return 0;
  return parseFloat(value.replace(/[^0-9.-]+/g, ''));
};

// Utility to format phone numbers
export const formatPhone = (value) => {
  if (!value) return '';
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
  if (match) {
    return '(' + match[1] + ') ' + match[2] + '-' + match[3];
  }
  return value;
};

// Utility to truncate text
export const truncate = (text, length = 50, suffix = '...') => {
  if (!text || text.length <= length) return text;
  return text.substring(0, length).trim() + suffix;
};

// Utility to capitalize first letter
export const capitalize = (text) => {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

// Utility to convert to title case
export const toTitleCase = (text) => {
  if (!text) return '';
  return text.toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
};

export default {
  // Date/Time
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,
  formatDateRange,
  getDateDifference,
  // Numbers/Currency
  formatCurrency,
  formatNumber,
  formatPercent,
  formatCompactNumber,
  formatFileSize,
  formatOrdinal,
  parseCurrency,
  parseNumber,
  // Text
  formatPhone,
  truncate,
  capitalize,
  toTitleCase,
};
