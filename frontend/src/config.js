// Central API configuration for local and deployed environments
const RAW_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_URL = RAW_URL.endsWith('/api/v1')
  ? RAW_URL
  : `${RAW_URL.replace(/\/$/, '')}/api/v1`;
