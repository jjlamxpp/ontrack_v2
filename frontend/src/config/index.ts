export const config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  ENV: import.meta.env.VITE_ENV || 'development'
};
